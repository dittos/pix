import * as React from "react"
import { useLoaderData } from "react-router-dom"

export const facesLoader = async () => {
  return fetch("/api/face-clusters")
    .then(r => r.json())
}

export const FacesRoute = () => {
  const clusters = useLoaderData() as any
  const [selected, setSelected] = React.useState<any>(null)
  const [cluster, setCluster] = React.useState<any>(null)
  React.useEffect(() => {
    if (selected) {
      fetch(`/api/face-clusters/${encodeURIComponent(selected.id)}`)
        .then(r => r.json())
        .then(r => setCluster(r))
    } else {
      setCluster(null)
    }
  }, [selected])

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col py-3">
          <div className="d-flex flex-wrap">
            {clusters.map((cluster: any) => {
              const face = cluster.faces[0]
              return (
                <div key={cluster.id} className="me-2 mb-2">
                  {cluster.label ?? cluster.id.substring(0, 8)} ({cluster.face_count})<br />
                  <div style={{
                    border: selected?.id === cluster.id ? '2px solid red' : ''
                  }} onClick={() => setSelected(cluster)}>
                    <img src={`/images/faces/${face.local_filename}`} style={{height: 120}} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {cluster && (
          <div className="col border-start p-3 vh-fill overflow-y-auto bg-body-tertiary">
            <h2>{cluster.label ?? cluster.id.substring(0, 8)}</h2>
            {cluster.wikidata_qid && <p><a href={`https://www.wikidata.org/entity/${cluster.wikidata_qid}`} target="_blank">{cluster.wikidata_qid}</a></p>}
            <p className="mb-4">total {cluster.face_count} faces in images</p>

            <SetLabelForm faceCluster={cluster} onUpdate={(c: any) => setCluster(c) /* TODO: update list */} />

            <div className="d-flex flex-wrap">
              {cluster.faces.map((face: any) => {
                return (
                  <div className="me-2 mb-2" key={`${face.local_filename}`}>
                    <img src={`/images/faces/${face.local_filename}`} style={{height: 120}} />
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const SetLabelForm = ({ faceCluster, onUpdate }: any) => {
  const [qid, setQid] = React.useState("")

  const submit: React.FormEventHandler = (event) => {
    event.preventDefault()

    fetch(`/api/face-clusters/${faceCluster.id}/label`, {
      method: 'PUT',
      body: JSON.stringify({wikidata_qid: qid}),
      headers: {'Content-Type': 'application/json'},
    }).then(r => {
      if (r.ok) return r.json()
      throw new Error()
    }).then(r => {
      onUpdate(r)
      setQid("")
    }).catch(e => alert(e.message))
  }

  return (
    <form onSubmit={submit}>
      <input type="text" placeholder="Wikidata QID (ex: Q1234)" value={qid} onChange={(event) => setQid(event.target.value)} />
      <button type="submit" className="btn btn-primary">Link</button>
    </form>
  )
}
