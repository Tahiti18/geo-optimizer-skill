const assetBase = '/assets/geoready-visuals';

export const marketingVisuals = {
  commandCenter: {
    webp: `${assetBase}/ai-visibility-command-center.webp`,
    webpSrcSet: [
      `${assetBase}/ai-visibility-command-center-800.webp 800w`,
      `${assetBase}/ai-visibility-command-center-1200.webp 1200w`,
      `${assetBase}/ai-visibility-command-center.webp 1672w`,
    ].join(', '),
    png: `${assetBase}/ai-visibility-command-center.png`,
    alt: 'GeoReady audit dashboard with a GEO score, crawler access matrix, citation graph, recommendations, and trend history.',
    caption: 'GeoReady audit view: GEO score, crawler access, citation graph, recommendations, and score trend in one report.',
    width: 1672,
    height: 941,
  },
  discoveryStack: {
    webp: `${assetBase}/ai-discovery-stack.webp`,
    webpSrcSet: [
      `${assetBase}/ai-discovery-stack-800.webp 800w`,
      `${assetBase}/ai-discovery-stack-1200.webp 1200w`,
      `${assetBase}/ai-discovery-stack.webp 1672w`,
    ].join(', '),
    png: `${assetBase}/ai-discovery-stack.png`,
    alt: 'Layered AI visibility model with crawler access, llms.txt, schema, content blocks, entity graph, and citation output.',
    caption: 'AI visibility stack: access, structure, entity clarity, and citation output. The image is illustrative; the audit score comes from the GEO Optimizer rules.',
    width: 1672,
    height: 941,
  },
  monitoring: {
    webp: `${assetBase}/monitoring-alerts-dashboard.webp`,
    webpSrcSet: [
      `${assetBase}/monitoring-alerts-dashboard-800.webp 800w`,
      `${assetBase}/monitoring-alerts-dashboard-1200.webp 1200w`,
      `${assetBase}/monitoring-alerts-dashboard.webp 1448w`,
    ].join(', '),
    png: `${assetBase}/monitoring-alerts-dashboard.png`,
    alt: 'GeoReady monitoring dashboard with score history, regression alert, domain portfolio, and AI answer snapshot status.',
    caption: 'Monitoring turns one audit into an ongoing signal: score history, portfolio checks, regression alerts, and AI answer snapshots.',
    width: 1448,
    height: 1086,
  },
  citationChecker: {
    webp: `${assetBase}/ai-citation-checker.webp`,
    webpSrcSet: [
      `${assetBase}/ai-citation-checker-800.webp 800w`,
      `${assetBase}/ai-citation-checker-1200.webp 1200w`,
      `${assetBase}/ai-citation-checker.webp 1536w`,
    ].join(', '),
    png: `${assetBase}/ai-citation-checker.png`,
    alt: 'AI citation checker interface with domain input, answer snapshots, citation chips, and citation rate metric.',
    caption: 'Citation checker view: ask category questions, inspect cited domains, and see whether your own domain appears as a source.',
    width: 1536,
    height: 1024,
  },
  clientReport: {
    webp: `${assetBase}/client-report-export.webp`,
    webpSrcSet: [
      `${assetBase}/client-report-export-800.webp 800w`,
      `${assetBase}/client-report-export-1200.webp 1200w`,
      `${assetBase}/client-report-export.webp 1448w`,
    ].join(', '),
    png: `${assetBase}/client-report-export.png`,
    alt: 'GeoReady report export package with score breakdown, recommendations, and client-ready PDF report.',
    caption: 'Client-ready reporting: score breakdown, recommendations, and PDF export for audit deliverables.',
    width: 1448,
    height: 1086,
  },
} as const;
