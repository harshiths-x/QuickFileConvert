import Link from "next/link";
export default function NotFound() { return <div className="container not-found"><h1>Page not found</h1><p>This tool or page does not exist.</p><Link className="button button-primary" href="/">Back to tools</Link></div>; }
