export function Table({ children }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-300 rounded-lg text-sm text-left text-gray-600">
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children }) {
  return <thead className="bg-gray-100 text-gray-700 text-sm">{children}</thead>;
}

export function TableBody({ children }) {
  return <tbody className="divide-y divide-gray-200">{children}</tbody>;
}

export function TableRow({ children }) {
  return <tr className="hover:bg-gray-50 transition-colors">{children}</tr>;
}

export function TableHead({ children }) {
  return <th className="px-4 py-2 font-medium border-b">{children}</th>;
}

export function TableCell({ children }) {
  return <td className="px-4 py-2 whitespace-nowrap">{children}</td>;
}