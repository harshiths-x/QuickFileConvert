import Link from "next/link";
import { FileText } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";

export function Header() {
  return <header className="site-header"><div className="container header-inner">
    <Link href="/" className="brand" aria-label="QuickFileConvert home"><span className="brand-mark"><FileText size={19} strokeWidth={2.2} /></span><span>QuickFileConvert</span></Link>
    <nav aria-label="Main navigation" className="nav"><Link href="/#tools">Tools</Link><ThemeToggle /></nav>
  </div></header>;
}
