declare module 'react-cytoscapejs' {
  import type { CSSProperties } from 'react'
  import type {
    Core,
    ElementDefinition,
    LayoutOptions,
    Stylesheet,
  } from 'cytoscape'

  export interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    layout?: LayoutOptions
    stylesheet?: Stylesheet[]
    style?: CSSProperties
    className?: string
    cy?: (cy: Core) => void
    minZoom?: number
    maxZoom?: number
    zoom?: number
    pan?: { x: number; y: number }
    boxSelectionEnabled?: boolean
    autoungrabify?: boolean
    autounselectify?: boolean
    userZoomingEnabled?: boolean
    userPanningEnabled?: boolean
  }

  const CytoscapeComponent: ((props: CytoscapeComponentProps) => JSX.Element) & {
    normalizeElements: (elements: {
      nodes?: ElementDefinition[]
      edges?: ElementDefinition[]
    }) => ElementDefinition[]
  }
  export default CytoscapeComponent
}

declare module 'cytoscape-cose-bilkent' {
  import type { Ext } from 'cytoscape'
  const ext: Ext
  export default ext
}
