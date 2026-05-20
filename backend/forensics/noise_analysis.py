from __future__ import annotations

import cv2
import numpy as np

_INCONSISTENCY_THRESHOLD = 25.0

_OUTLIER_Z_THRESHOLD = 2.0


def analyze_noise(
    image: np.ndarray,
    blur_kernel: int = 3,
    grid_rows: int = 4,
    grid_cols: int = 4,
) -> dict | None:
    
    try:
        if image is None or image.size == 0:
            return None

        assert isinstance(blur_kernel, int), (
            f"blur_kernel must be int, got {type(blur_kernel)}"
        )
        if blur_kernel < 1:
            blur_kernel = 3
        if blur_kernel % 2 == 0:
            blur_kernel += 1

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        blurred = cv2.GaussianBlur(
            gray,
            (blur_kernel, blur_kernel),
            0,
        )

        noise_residual = (
            gray.astype(np.float32) - blurred.astype(np.float32)
        )

        overall_mean = float(np.mean(noise_residual))
        overall_std = float(np.std(noise_residual))

        height, width = noise_residual.shape[:2]
        eff_rows = min(grid_rows, height)
        eff_cols = min(grid_cols, width)

        cell_h = height // eff_rows
        cell_w = width // eff_cols

        region_means: list[list[float]] = []
        flat_means: list[float] = []

        for r in range(eff_rows):
            row_means: list[float] = []
            for c in range(eff_cols):
                
                y_start = r * cell_h
                y_end = (
                    y_start + cell_h
                    if r < eff_rows - 1
                    else height
                )
                x_start = c * cell_w
                x_end = (
                    x_start + cell_w
                    if c < eff_cols - 1
                    else width
                )

                cell = noise_residual[y_start:y_end, x_start:x_end]

                cell_mean = float(np.mean(np.abs(cell)))
                row_means.append(round(cell_mean, 4))
                flat_means.append(cell_mean)

            region_means.append(row_means)

        regional_var = (
            float(np.var(flat_means)) if flat_means else 0.0
        )
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = float(np.var(laplacian))

        mean_intensity = float(np.mean(gray))

        is_inconsistent = regional_var > _INCONSISTENCY_THRESHOLD

        return {
            "noise_mean": round(overall_mean, 4),
            "noise_std": round(overall_std, 4),
            "regional_variance": round(regional_var, 4),
            "laplacian_variance": round(laplacian_var, 4),
            "region_grid": region_means,
            "mean_intensity": round(mean_intensity, 4),
            "is_inconsistent": is_inconsistent,
            "error": None,
        }

    except Exception:
        return None


def compare_pages(page_results: list[dict]) -> dict:
    
    default = {
        "cross_page_variance": 0.0,
        "outlier_pages": [],
        "is_suspicious": False,
        "issues": [],
    }

    try:
        if len(page_results) < 2:
            return default

        indexed_values: list[tuple[int, float]] = []
        for idx, result in enumerate(page_results):
            if result is None:
                continue
            val = result.get("laplacian_variance")
            if val is not None:
                indexed_values.append((idx, float(val)))

        if len(indexed_values) < 2:
            return default

        values = np.array(
            [v for _, v in indexed_values], dtype=np.float64
        )
        group_mean = float(np.mean(values))
        group_std = float(np.std(values))
        cross_page_var = float(np.var(values))

        outlier_pages: list[int] = []

        if group_std > 0:
            for page_idx, val in indexed_values:
                z_score = abs(val - group_mean) / group_std
                if z_score > _OUTLIER_Z_THRESHOLD:
                    outlier_pages.append(page_idx)

        is_suspicious = len(outlier_pages) > 0

        issues: list[str] = []
        if is_suspicious:
            page_nums = ", ".join(
                str(p + 1) for p in outlier_pages
            )
            issues.append(
                f"Significant visual inconsistency across "
                f"pages suggests pages from different sources. "
                f"Outlier page(s): {page_nums}."
            )

        return {
            "cross_page_variance": round(cross_page_var, 4),
            "outlier_pages": outlier_pages,
            "is_suspicious": is_suspicious,
            "issues": issues,
        }

    except Exception:
        return default
