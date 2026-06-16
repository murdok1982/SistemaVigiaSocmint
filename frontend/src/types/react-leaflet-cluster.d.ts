declare module 'react-leaflet-cluster' {
  import type { ReactNode } from 'react'
  import type { MarkerClusterGroupOptions } from 'leaflet'

  export interface MarkerClusterGroupProps extends MarkerClusterGroupOptions {
    children?: ReactNode
    chunkedLoading?: boolean
    showCoverageOnHover?: boolean
    spiderfyOnMaxZoom?: boolean
    zoomToBoundsOnClick?: boolean
    maxClusterRadius?: number
  }

  const MarkerClusterGroup: (props: MarkerClusterGroupProps) => JSX.Element
  export default MarkerClusterGroup
}

declare module 'leaflet' {
  interface MarkerClusterGroupOptions {
    showCoverageOnHover?: boolean
    zoomToBoundsOnClick?: boolean
    spiderfyOnMaxZoom?: boolean
    maxClusterRadius?: number
    chunkedLoading?: boolean
  }
}
