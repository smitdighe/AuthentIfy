/**
 * Minimal site footer for AuthentIfy.
 * @returns {JSX.Element}
 */
export default function Footer() {
  return (
    <footer
      className="flex flex-col sm:flex-row items-center justify-between px-6 lg:px-10 py-6 text-sm font-body"
      style={{
        background: 'rgba(176, 210, 210,0.5)',
        borderTop: '1px solid rgba(226,232,240,0.08)',
        color: 'rgba(226,232,240,0.4)',
      }}
    >
      <span>© 2026 AuthentIfy — Verify before you trust.</span>
      <span className="mt-2 sm:mt-0">Built with Python + React</span>
    </footer>
  );
}
