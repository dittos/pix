import { useEffect, useState } from "react";

export function useListUpdater<T>(routeData: T[], keyExtractor: (obj: T) => string): [T[], (obj: T) => void] {
  const [data, setData] = useState<T[]>(routeData)
  useEffect(() => {
    setData(routeData)
  }, [routeData])
  const updater = (update: T) => {
    const updateKey = keyExtractor(update)
    setData(data.map(obj => keyExtractor(obj) === updateKey ? update : obj))
  }
  return [data, updater]
}
