import type { Vulnerability } from "../api";

export function WeaknessesView({ items }: { items: Vulnerability[] }) {
  return (
    <div className="view">
      <div className="vhead">
        <div>
          <h2>Planted weaknesses</h2>
          <p>Each tagged with its OWASP:2025 category, ATT&CK technique and lecture.</p>
        </div>
      </div>
      <div className="panel">
        <table className="tbl cat">
          <thead>
            <tr>
              <th>ID</th>
              <th>Weakness</th>
              <th>OWASP:2025</th>
              <th>ATT&CK</th>
              <th>Lecture</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td>Catalog unavailable.</td>
              </tr>
            )}
            {items.map((v) => (
              <tr key={v.id}>
                <td className="id">{v.id}</td>
                <td className="w">
                  {v.name}
                  <div className="csub">{v.note}</div>
                </td>
                <td className="code">{v.owasp_2025}</td>
                <td className="code">{v.attack}</td>
                <td className="code">{v.course}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
