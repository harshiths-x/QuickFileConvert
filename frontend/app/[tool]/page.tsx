import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Converter } from "@/components/converter";
import { getTool, tools } from "@/lib/tools";

export function generateStaticParams() { return tools.map(tool => ({ tool: tool.slug })); }
export async function generateMetadata({ params }: { params: Promise<{ tool: string }> }): Promise<Metadata> {
  const tool = getTool((await params).tool);
  return { title: tool?.title || "Tool", description: tool?.description };
}
export default async function ToolPage({ params }: { params: Promise<{ tool: string }> }) {
  const tool = getTool((await params).tool);
  if (!tool) notFound();
  return <Converter tool={tool} />;
}
