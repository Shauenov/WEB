export function ListCards({
  title,
  items,
  render,
}: {
  title: string;
  items: any[];
  render: (i: any) => JSX.Element;
}) {
  return (
    <section style={{ marginBottom: 24 }}>
      <h3>{title}</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
        {items.map(render)}
      </div>
    </section>
  );
}
