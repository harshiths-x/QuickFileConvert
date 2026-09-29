export type Tool = {
  slug: string;
  title: string;
  description: string;
  accept: string;
  input: string;
  output: string;
  category: "Documents" | "PDF tools" | "Images" | "Spreadsheets";
  icon: "file" | "pdf" | "image" | "sheet";
  option?: "pages" | "rotate" | "reorder" | "sheet";
};

export const tools: Tool[] = [
  { slug: "pdf-to-word", title: "PDF to Word", description: "Turn a PDF into an editable Word document.", accept: ".pdf", input: "PDF", output: "DOCX", category: "Documents", icon: "file" },
  { slug: "word-to-pdf", title: "Word to PDF", description: "Create a shareable PDF from a Word document.", accept: ".docx", input: "DOCX", output: "PDF", category: "Documents", icon: "file" },
  { slug: "pdf-to-txt", title: "PDF to TXT", description: "Extract readable text from a PDF.", accept: ".pdf", input: "PDF", output: "TXT", category: "Documents", icon: "file" },
  { slug: "txt-to-pdf", title: "TXT to PDF", description: "Make a clean PDF from a text file.", accept: ".txt", input: "TXT", output: "PDF", category: "Documents", icon: "file" },
  { slug: "docx-to-txt", title: "DOCX to TXT", description: "Save Word document text as a plain text file.", accept: ".docx", input: "DOCX", output: "TXT", category: "Documents", icon: "file" },
  { slug: "pdf-split", title: "Split PDF", description: "Keep one continuous range of PDF pages.", accept: ".pdf", input: "PDF", output: "PDF", category: "PDF tools", icon: "pdf", option: "pages" },
  { slug: "pdf-rotate", title: "Rotate PDF", description: "Rotate all or selected pages.", accept: ".pdf", input: "PDF", output: "PDF", category: "PDF tools", icon: "pdf", option: "rotate" },
  { slug: "pdf-extract", title: "Extract PDF pages", description: "Create one PDF from chosen pages.", accept: ".pdf", input: "PDF", output: "PDF", category: "PDF tools", icon: "pdf", option: "pages" },
  { slug: "pdf-reorder", title: "Reorder PDF pages", description: "Set a new order for every page.", accept: ".pdf", input: "PDF", output: "PDF", category: "PDF tools", icon: "pdf", option: "reorder" },
  { slug: "jpg-to-png", title: "JPG to PNG", description: "Convert a JPEG image to PNG.", accept: ".jpg,.jpeg", input: "JPG / JPEG", output: "PNG", category: "Images", icon: "image" },
  { slug: "png-to-jpg", title: "PNG to JPG", description: "Convert PNG with a white transparency background.", accept: ".png", input: "PNG", output: "JPG", category: "Images", icon: "image" },
  { slug: "image-to-pdf", title: "Image to PDF", description: "Place one image into a PDF.", accept: ".jpg,.jpeg,.png", input: "JPG / JPEG / PNG", output: "PDF", category: "Images", icon: "image" },
  { slug: "csv-to-excel", title: "CSV to Excel", description: "Turn a CSV into an Excel workbook.", accept: ".csv", input: "CSV", output: "XLSX", category: "Spreadsheets", icon: "sheet" },
  { slug: "excel-to-csv", title: "Excel to CSV", description: "Export a worksheet to CSV.", accept: ".xlsx", input: "XLSX", output: "CSV", category: "Spreadsheets", icon: "sheet", option: "sheet" },
];

export const categories = ["Documents", "PDF tools", "Images", "Spreadsheets"] as const;
export const getTool = (slug: string) => tools.find((tool) => tool.slug === slug);
export function apiUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_URL;
  if (!value) throw new Error("The backend URL is not configured.");
  return value.replace(/\/$/, "");
}
