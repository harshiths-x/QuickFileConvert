import Link from "next/link";
import { ArrowRight, Download, FileText, Image, Layers3, ShieldCheck, Table2, Upload } from "lucide-react";
import { categories, tools } from "@/lib/tools";

const icons = { file: FileText, pdf: Layers3, image: Image, sheet: Table2 };

export default function Home() {
  return <>
    <section className="hero container"><div className="eyebrow"><ShieldCheck size={15} /> Simple file tools, built for privacy</div><h1>Convert files<br /><span>quickly.</span></h1><p>Convert common documents, PDFs, images, and spreadsheets in a few clicks. No account required.</p><div className="hero-actions"><Link className="button button-primary" href="#tools">Choose a tool <ArrowRight size={17} /></Link><span>No account required</span></div><div className="hero-notes"><span>Files deleted within 5 minutes</span><span>Maximum 50 MB per file</span></div></section>
    <section id="tools" className="tools-section container"><div className="section-heading"><div><span className="section-kicker">TOOLS</span><h2>What would you like to do?</h2><p>Choose a tool to get started. One file at a time.</p></div></div>
      {categories.map(category => <div className="category" key={category}><h3>{category}</h3><div className="tool-grid">{tools.filter(tool => tool.category === category).map(tool => { const Icon = icons[tool.icon]; return <Link className="tool-card" href={`/${tool.slug}`} key={tool.slug}><span className="tool-icon"><Icon size={20} strokeWidth={1.9} /></span><strong>{tool.title}</strong><span>{tool.description}</span><ArrowRight className="card-arrow" size={17} /></Link>; })}</div></div>)}
    </section>
    <section className="how-section"><div className="container"><div className="section-heading"><div><span className="section-kicker">HOW IT WORKS</span><h2>Three simple steps</h2></div></div><div className="steps"><div><span className="step-icon"><Upload size={21} /></span><span className="step-number">01</span><h3>Upload</h3><p>Choose one file, up to 50 MB.</p></div><div><span className="step-icon"><Layers3 size={21} /></span><span className="step-number">02</span><h3>Convert</h3><p>We process it temporarily on the server.</p></div><div><span className="step-icon"><Download size={21} /></span><span className="step-number">03</span><h3>Download</h3><p>Save the result before it expires in 5 minutes.</p></div></div></div></section>
  </>;
}
