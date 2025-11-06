export default function Footer() {
  return (
    <footer className="mt-10 text-center py-6 glass-dark border-t border-white/10 select-none">
      <p className="text-gray-400 text-sm">
        © {new Date().getFullYear()} VoyagerAI — Built by <span className="text-blue-400">Team Odyssey</span>
      </p>
    </footer>
  );
}
