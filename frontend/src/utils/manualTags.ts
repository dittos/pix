import { useState } from "react";

const RecentlyAddedManualTagsKey = 'RecentlyAddedManualTags'
const RecentlyAddedManualTagsLimit = 10

export function useRecentlyAddedManualTags(): [string[], (tag: string) => void] {
  const [tags, setTags] = useState<string[]>(() => JSON.parse(window.localStorage.getItem(RecentlyAddedManualTagsKey) ?? '[]'))
  const addTag = (tag: string) => {
    const updated = [tag, ...tags.filter(t => t !== tag)].slice(0, RecentlyAddedManualTagsLimit)
    window.localStorage.setItem(RecentlyAddedManualTagsKey, JSON.stringify(updated))
    setTags(updated)
  }
  return [tags, addTag]
}
