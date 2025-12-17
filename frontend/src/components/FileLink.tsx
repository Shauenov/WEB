export function FileLink({ href, label }: { href?: string; label: string }) {
  if (!href) return <span style={{ color: "gray" }}>Нет ссылки</span>;
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {label}
    </a>
  );
}
