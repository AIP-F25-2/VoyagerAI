export default function Header() {
  return (
    <header className="p-4 bg-black/40 backdrop-blur-md border-b border-white/10 flex items-center justify-between sticky top-0 z-50 glass-dark">
      <h1 className="text-3xl font-extrabold text-white tracking-wide select-none">
        VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
      </h1>

      <div className="flex items-center space-x-4">
        <button className="px-4 py-1.5 border border-white/30 text-white rounded-lg hover:bg-white/20 transition hover:cursor-pointer">
          Sign In
        </button>
        <button className="px-4 py-1.5 border border-white/30 text-white rounded-lg hover:bg-blue-600/60 transition hover:cursor-pointer">
          Sign Up
        </button>
      </div>
    </header>
  );
}
