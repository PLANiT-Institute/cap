import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { theoryDoc, theorySlugs } from "../../../lib/data";

export function generateStaticParams() {
  return theorySlugs().map((slug) => ({ slug }));
}

export default async function TheoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const md = theoryDoc(slug);
  return (
    <article style={{ lineHeight: 1.75, maxWidth: 760 }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
    </article>
  );
}
