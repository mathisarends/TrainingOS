import { LitElement, html, svg } from 'lit';

export interface ChartItem {
  label: string;
  value: number;
}
export class ValueChart extends LitElement {
  static properties = {
    items: { attribute: false },
    unit: { attribute: false },
    label: { type: String },
  };
  items: ChartItem[] = [];
  unit = 'kg';
  label = '';
  createRenderRoot() {
    return this;
  }
  render() {
    if (!this.items.length) return html`<div class="chart-empty">Noch keine Werte vorhanden</div>`;
    const width = 600,
      height = 270,
      left = 52,
      bottom = 38,
      top = 15;
    const max = Math.ceil((Math.max(...this.items.map((i) => i.value)) * 1.1) / 10) * 10 || 10;
    const plotHeight = height - bottom - top;
    const step = (width - left - 15) / this.items.length;
    return html`<figure class="value-chart">
      <figcaption>${this.label}</figcaption>
      <svg
        viewBox=${`0 0 ${width} ${height}`}
        role="img"
        aria-label=${`${this.label}: ${this.items.map((i) => `${i.label}, ${i.value} ${this.unit}`).join('; ')}`}
      >
        ${Array.from({ length: 5 }, (_, i) => {
          const value = (max * i) / 4,
            y = height - bottom - (value / max) * plotHeight;
          return svg`<line x1=${left} x2=${width - 15} y1=${y} y2=${y} class="chart-grid-line"/><text x=${left - 10} y=${y + 4} text-anchor="end" class="chart-label">${Math.round(value)}</text>`;
        })}
        ${this.items.map((item, i) => {
          const x = left + i * step + step * 0.2,
            h = (item.value / max) * plotHeight;
          return svg`<rect x=${x} y=${height - bottom - h} width=${step * 0.6} height=${h} rx="2" class="chart-bar"><title>${item.label}: ${item.value} ${this.unit}</title></rect>${i % Math.max(1, Math.ceil(this.items.length / 8)) === 0 ? svg`<text x=${x + step * 0.3} y=${height - 12} text-anchor="middle" class="chart-label">${item.label}</text>` : svg``}`;
        })}
      </svg>
    </figure>`;
  }
}
customElements.define('value-chart', ValueChart);
