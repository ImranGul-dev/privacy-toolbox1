function displayName(item: any) {
  const category = item?.category || 'Metadata';
  const key = item?.key || item?.raw_key || '';
  if (!key || key === category) return category;
  return `${category}: ${key}`;
}

export function MetadataTagList({ items = [], emptyText = 'No removable private metadata found by current scanners.' }: { items?: any[]; emptyText?: string }) {
  if (!items.length) return <p className="text-sm text-subtle">{emptyText}</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {items.slice(0, 18).map((item, idx) => (
        <span key={`${item.key || item.category}-${idx}`} className="badge badge-amber" title={item.value_preview || item.detail || ''}>
          {displayName(item)}
        </span>
      ))}
    </div>
  );
}
