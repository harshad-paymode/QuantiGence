import Image from "next/image";

export default function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950">
      {/* LOGO SECTION */}
      <div className="flex items-center gap-3">
        {/* Your Uploaded Logo Image */}
        <div className="relative h-8 w-8">
          <Image 
            src="/logo_2.png" 
            alt="QuantiGence Logo" 
            fill
            className="object-contain"
          />
        </div>

        {/* The Logo Text - Pure White */}
        <div className="text-xl font-bold tracking-tighter text-white">
          QuantiGence
        </div>
      </div>

      {/* PROFILE CIRCLE */}
      <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-medium text-slate-400">
        HP
      </div>
    </header>
  );
}