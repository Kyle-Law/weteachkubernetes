"""Article content for blog.weteachkubernetes.com.

One entry per roadmap checkpoint. Edit the prose here and re-run scripts/build_blog.py,
or edit the generated HTML directly - both work, but only this file survives a rebuild.
"""

D = '2026-10-08'

ARTICLES = [

# ---------------------------------------------------------------- foundations
{
 'node': 'containers-before-k8s', 'slug': 'containers-before-kubernetes',
 'title': 'Containers before Kubernetes', 'minutes': 8, 'added': D,
 'dek': 'Namespaces, cgroups and image layers by hand, so that pod behaviour stops looking '
        'like magic and starts looking like Linux.',
 'body': [
  ('p', 'Almost every confusing thing Kubernetes does to a container is something Linux was '
        'already doing. If you learn the orchestrator first, you end up memorising behaviour. '
        'If you spend an afternoon below it, the same behaviour becomes obvious.'),
  ('h2', 'A container is three kernel features and a chroot'),
  ('p', 'There is no <code>container</code> object in the Linux kernel. What you get instead is '
        'a process with a restricted view of the system, assembled from namespaces, cgroups and '
        'a mounted filesystem. You can build one by hand:'),
  ('code', '''# a new PID, mount, UTS and network namespace, with a shell inside it
sudo unshare --pid --mount --uts --net --fork --mount-proc bash

# inside: you are process 1, and you can see almost nothing
ps aux
hostname container-by-hand
ip addr          # just lo - no route out, because nothing was plugged in yet'''),
  ('p', 'That last line is the whole of pod networking in miniature. A fresh network namespace '
        'has a loopback interface and nothing else. Something outside has to create a virtual '
        'ethernet pair, move one end in, and add routes. On a Kubernetes node, that something is '
        'the CNI plugin.'),
  ('h2', 'cgroups are why your pod was killed'),
  ('p', 'Namespaces control what a process can <em>see</em>. Control groups control what it can '
        '<em>use</em>. On cgroup v2 the interface is a filesystem:'),
  ('code', '''sudo mkdir /sys/fs/cgroup/demo
echo "100M" | sudo tee /sys/fs/cgroup/demo/memory.max
echo $$    | sudo tee /sys/fs/cgroup/demo/cgroup.procs

# now allocate more than that in this shell and watch what happens
cat /sys/fs/cgroup/demo/memory.events     # look at oom_kill'''),
  ('gotcha', '<b>This is the actual mechanism behind OOMKilled.</b> A memory limit in a pod spec '
             'becomes <code>memory.max</code> on a cgroup. When the process crosses it, the kernel '
             'OOM killer acts — not the kubelet, not the scheduler. That is why the container exits '
             'with code 137 and your application logs show nothing: it was not asked to stop.'),
  ('p', 'CPU behaves differently, and the difference matters. A CPU limit becomes a quota per '
        'period, so exceeding it does not kill anything — it throttles. A pod that is slow but '
        'alive is almost always CPU throttling; a pod that dies abruptly is almost always memory.'),
  ('h2', 'Images are layers, and layers are a tax'),
  ('p', 'An image is an ordered stack of tarballs plus a JSON manifest. Each instruction in a '
        'Dockerfile that changes the filesystem adds a layer, and layers are immutable — so '
        'deleting a file in a later layer hides it without reclaiming the space.'),
  ('code', '''# where the size actually went
docker history --no-trunc --format '{{.Size}}\\t{{.CreatedBy}}' your-image:tag | head -20'''),
  ('p', 'This stops being an aesthetic concern the moment you work on anything with CUDA or a '
        'model in it. A 12&nbsp;GB image is 12&nbsp;GB pulled onto every node that has to run it, '
        'before your process starts. It is the single most common reason a GPU pod appears to '
        '"hang" on first schedule — it is not hanging, it is pulling.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Run the <code>unshare</code> command above once. Ten minutes, and network policy '
          'later will make sense.',
          'Put a <code>memory.max</code> on a shell and get OOM-killed deliberately, so you '
          'recognise it in production.',
          'Run <code>docker history</code> on the largest image you own, and find the one layer '
          'that is most of it.',
          'Multi-stage builds: compile in one stage, copy only the artefact into a slim final '
          'stage. Usually the single biggest win available.']),
  ('p', 'Everything above is a property of Linux, not of Kubernetes. That is the point — it is '
        'all still true three abstractions up.'),
 ],
},
{
 'node': 'object-model', 'slug': 'the-api-object-model',
 'title': 'The API object model', 'minutes': 9, 'added': D,
 'dek': 'Why everything is a resource, what the control loop actually does, and how to read '
        'any CRD you meet later without waiting for someone to document it.',
 'body': [
  ('p', 'Kubernetes has one idea in it, repeated. You write down what you want, a controller '
        'compares that to what exists, and it acts to close the gap. Learn the shape of that '
        'loop and every new resource you meet — from a Deployment to a CiliumNetworkPolicy to '
        'something your colleague invented last week — is recognisable on sight.'),
  ('h2', 'Spec is a wish. Status is a measurement.'),
  ('p', 'Nearly every object has the same four parts: <code>apiVersion</code> and <code>kind</code> '
        'to say what it is, <code>metadata</code> to name it, <code>spec</code> for what you want, '
        'and <code>status</code> for what is true. You write spec. Controllers write status. '
        'Confusing the two is the most common beginner mistake, and the reason editing status by '
        'hand does nothing useful.'),
  ('code', '''kubectl get deploy my-app -o jsonpath='{.spec.replicas}'       # what you asked for
kubectl get deploy my-app -o jsonpath='{.status.readyReplicas}'  # what you have'''),
  ('h2', 'The loop, in one paragraph'),
  ('p', 'A controller watches a resource type. When one changes, it is put on a work queue. The '
        'controller reads the current world, computes the difference from spec, and takes one '
        'step towards closing it — then it does that again, forever. It must be safe to run the '
        'same reconcile twice, because it will be. Nothing in the system assumes a message is '
        'delivered exactly once.'),
  ('p', 'This is why Kubernetes recovers from almost anything you do to it, and also why it '
        'sometimes does nothing at all and gives you no error: the controller may simply not be '
        'watching the thing you changed.'),
  ('h2', 'Read the API, not the blog post'),
  ('p', 'The cluster documents itself, including every CRD installed on it. Three commands cover '
        'most of what you would otherwise go searching for:'),
  ('code', '''kubectl api-resources                    # everything this cluster knows about
kubectl explain deployment.spec.strategy --recursive
kubectl get crd                          # what has been added beyond core Kubernetes'''),
  ('note', '<b>This is the single most useful habit on the list.</b> <code>kubectl explain</code> '
           'reads the OpenAPI schema out of the API server, so it is correct for <em>your</em> '
           'cluster at <em>your</em> version, which a search result is not. It also works on '
           'custom resources the moment someone installs them.'),
  ('h2', 'Ownership is how deletion works'),
  ('p', 'A Deployment does not manage pods. It manages a ReplicaSet, which manages pods, and each '
        'child carries an <code>ownerReferences</code> entry pointing at its parent. Delete the '
        'parent and garbage collection removes the children.'),
  ('code', '''kubectl get rs -l app=my-app -o jsonpath='{.items[*].metadata.ownerReferences[*].kind}'

# orphan the children instead of deleting them - occasionally what you want in an incident
kubectl delete deploy my-app --cascade=orphan'''),
  ('h2', 'Labels do the wiring'),
  ('p', 'There are no pointers in a Kubernetes manifest. A Service finds pods because its '
        '<code>selector</code> matches their labels, and nothing validates that the match '
        'succeeds. A Service with a typo in its selector is a perfectly valid object with zero '
        'endpoints.'),
  ('code', '''# the real question when a Service returns nothing
kubectl get endpointslices -l kubernetes.io/service-name=my-svc'''),
  ('gotcha', '<b>An empty EndpointSlice means the selector matched nothing, or nothing matched is '
             'ready.</b> Those two causes look identical from the Service and are fixed in '
             'completely different places — one is a label typo, the other is a failing readiness '
             'probe. Check the pods before you touch the Service.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Pick any resource in your cluster and read its <code>status</code> alongside its '
          '<code>spec</code>. Notice which fields you never wrote.',
          'Run <code>kubectl explain</code> on something you thought you knew — '
          '<code>pod.spec.securityContext</code> is a good one.',
          'Break a Service selector on purpose and follow it down to the EndpointSlice.']),
 ],
},

# ---------------------------------------------------------------- workloads
{
 'node': 'deployments-probes', 'slug': 'deployments-probes-and-rollouts',
 'title': 'Deployments, probes and rollouts', 'minutes': 10, 'added': D,
 'dek': 'Rolling updates that do not drop traffic, and the three probes people keep confusing.',
 'body': [
  ('p', 'A rolling update is the most routine thing a cluster does and the most common source of '
        'self-inflicted downtime. The default settings are reasonable; they are just not the '
        'settings most applications need, and the gap shows up only under real traffic.'),
  ('h2', 'Three probes, three different jobs'),
  ('ul', ['<strong>startupProbe</strong> — "has it finished booting?" While this is failing, the '
          'other two are not run at all.',
          '<strong>readinessProbe</strong> — "should it receive traffic?" Failing removes the pod '
          'from Service endpoints. It does not restart anything.',
          '<strong>livenessProbe</strong> — "is it wedged?" Failing <em>kills the container</em>.']),
  ('gotcha', '<b>The classic outage: using a slow livenessProbe as a startup check.</b> An '
             'application that takes 90 seconds to warm up, with a livenessProbe that starts '
             'checking at 30 seconds, will be killed and restarted forever — and it will never '
             'once report an error, because it never got to finish starting. That is what '
             '<code>startupProbe</code> exists for.'),
  ('code', '''startupProbe:                 # generous: booting is allowed to be slow
  httpGet: { path: /healthz, port: 8080 }
  failureThreshold: 30
  periodSeconds: 5             # up to 150s to start, checked every 5s

readinessProbe:               # strict: reflects whether dependencies are usable
  httpGet: { path: /ready, port: 8080 }
  periodSeconds: 5

livenessProbe:                # conservative: only true deadlock should trip this
  httpGet: { path: /healthz, port: 8080 }
  periodSeconds: 10
  failureThreshold: 6'''),
  ('p', 'A useful rule: <code>/ready</code> may check the database, the cache, the thing you '
        'cannot work without. <code>/healthz</code> must check nothing external. If liveness '
        'depends on your database, a database blip restarts every pod you own at once, which '
        'turns a brief degradation into a cold-start stampede.'),
  ('h2', 'maxUnavailable is the dial that matters'),
  ('code', '''spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0        # never go below 6 serving pods
      maxSurge: 2              # briefly run up to 8'''),
  ('p', 'The default is 25% of each. With <code>maxUnavailable: 25%</code> and four replicas you '
        'are deliberately running on three during every deploy, which is fine until the deploy '
        'coincides with a traffic peak. Setting it to <code>0</code> with some surge costs you a '
        'little headroom and removes a whole category of deploy-time incidents.'),
  ('h2', 'Termination is not instant, and the gap bites'),
  ('p', 'When a pod is deleted, two things happen at the same time: the kubelet sends '
        '<code>SIGTERM</code>, and the endpoint controller starts removing it from Services. '
        'Those are not synchronised. For a second or two, a pod that is already shutting down is '
        'still receiving new connections.'),
  ('code', '''lifecycle:
  preStop:
    exec:
      command: ["sleep", "5"]   # keep serving while endpoints propagate
terminationGracePeriodSeconds: 30'''),
  ('p', 'A <code>preStop</code> sleep looks crude and is the standard fix. The pod stays up and '
        'keeps serving for a few seconds after it is marked for deletion, by which time the '
        'proxies have stopped sending it work. Then your application gets its <code>SIGTERM</code> '
        'and can drain cleanly.'),
  ('h2', 'Watching a rollout properly'),
  ('code', '''kubectl rollout status deploy/my-app --timeout=120s
kubectl rollout history deploy/my-app
kubectl rollout undo deploy/my-app --to-revision=3

# why is it stuck? the Deployment tells you, in conditions
kubectl get deploy my-app -o jsonpath='{.status.conditions[*].message}{"\\n"}' '''),
  ('p', 'A stalled rollout usually reports <code>ProgressDeadlineExceeded</code>, which means new '
        'pods never became ready within 10 minutes. The Deployment is not the thing to debug at '
        'that point — the new pod is.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Set <code>maxUnavailable: 0</code> on anything that serves users.',
          'Add a <code>startupProbe</code> to anything slow, and make the liveness check depend '
          'on nothing external.',
          'Add a five-second <code>preStop</code> sleep and watch your deploy-time error rate '
          'change.',
          'Break a rollout on purpose, then read <code>.status.conditions</code> rather than '
          'guessing.']),
 ],
},
{
 'node': 'config-secrets', 'slug': 'config-secrets-and-the-edge-cases',
 'title': 'Config, secrets and the twelve-factor edge cases', 'minutes': 8, 'added': D,
 'dek': 'ConfigMap reload behaviour, projected volumes, and why your Secret is base64 and '
        'not encrypted.',
 'body': [
  ('p', 'Configuration is the part of Kubernetes that appears finished after an hour and then '
        'produces a confusing incident six months later. Two behaviours cause most of them.'),
  ('h2', 'Your ConfigMap did not reload, and that is by design'),
  ('p', 'How a ConfigMap reaches your container determines whether it can ever change:'),
  ('ul', ['<strong>As environment variables</strong> — resolved once, at container start. '
          'Updating the ConfigMap changes nothing until the pod is replaced. Ever.',
          '<strong>As a mounted volume</strong> — the kubelet refreshes the files, eventually. '
          'Up to about a minute by default, and your process still has to notice and re-read '
          'them.',
          '<strong>With <code>subPath</code></strong> — <em>never</em> updates. This is the one '
          'that catches people.']),
  ('gotcha', '<b>A <code>subPath</code> mount is a one-time copy.</b> It is extremely common, '
             'because it is how you put a single config file into a directory that already has '
             'other things in it — and it silently opts you out of all updates. If a file must '
             'be reloadable, mount the whole volume into its own directory and symlink, or accept '
             'that the pod has to restart.'),
  ('code', '''# force a restart on config change: hash the config into the pod template
kubectl rollout restart deploy/my-app

# or, the declarative version - annotate with a checksum so the template itself changes
# annotations:
#   config/checksum: "{{ sha256sum of the ConfigMap }}"'''),
  ('p', 'That annotation trick is what Helm charts do, and it is worth copying even if you do not '
        'use Helm. It converts "config changed but nothing happened" into an ordinary rollout.'),
  ('h2', 'A Secret is not encrypted'),
  ('p', 'Secret data is base64-encoded, which is an encoding, not a protection. Anyone who can '
        'read the Secret can read the value:'),
  ('code', '''kubectl get secret db -o jsonpath='{.data.password}' | base64 -d'''),
  ('p', 'Two things follow. First, the real control is RBAC — who can <code>get</code> Secrets in '
        'that namespace, and who can create a pod that mounts them. Second, by default they are '
        'stored in etcd as plaintext, so an etcd backup is a credential dump. Encryption at rest '
        'is a cluster-level setting you have to turn on deliberately.'),
  ('ul', ['Prefer mounted files over environment variables: env vars leak into crash dumps, '
          'child processes and <code>/proc/&lt;pid&gt;/environ</code>.',
          'Never <code>kubectl describe</code> a pod into a shared channel without checking what '
          'is in it.',
          'For anything serious, keep the source of truth outside the cluster and sync it in — '
          'External Secrets Operator or the CSI secrets driver — so rotation happens in one '
          'place.']),
  ('h2', 'Projected volumes are underused'),
  ('p', 'You can assemble one directory out of several sources, which keeps application code '
        'from caring where anything came from:'),
  ('code', '''volumes:
  - name: config
    projected:
      sources:
        - configMap: { name: app-config }
        - secret:    { name: app-secrets }
        - serviceAccountToken:          # short-lived, audience-scoped
            path: token
            expirationSeconds: 3600
            audience: vault'''),
  ('p', 'That last source is the one worth knowing. A projected ServiceAccount token is '
        'time-limited and bound to an audience, so a leaked token expires and is only accepted by '
        'the service it was minted for. It is the basis of every sane workload-identity setup, '
        'and it replaces long-lived mounted tokens.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Find every <code>subPath</code> mount you own and decide whether it needs to be '
          'reloadable.',
          'Move secrets from <code>env</code> to mounted files on your most sensitive service.',
          'Check whether encryption at rest is enabled on your cluster. Assume it is not until '
          'you have looked.']),
 ],
},
{
 'node': 'gitops-delivery', 'slug': 'declarative-delivery',
 'title': 'Declarative delivery', 'minutes': 9, 'added': D,
 'dek': 'Kustomize overlays and a pull-based reconciler, so environments stop drifting '
        'silently and a cluster can be rebuilt from Git alone.',
 'body': [
  ('p', 'The test of a delivery setup is not how fast it deploys. It is whether you can delete '
        'the cluster and get it back. If the answer involves anyone remembering anything, the '
        'answer is no.'),
  ('h2', 'Push and pull are different trust models'),
  ('p', 'A push pipeline holds cluster credentials in CI and runs <code>kubectl apply</code>. A '
        'pull reconciler runs <em>inside</em> the cluster, watches Git, and applies what it finds. '
        'The second is usually better, for a reason that has nothing to do with features: CI '
        'never needs cluster credentials, so a compromised CI runner cannot reach production.'),
  ('p', 'Pull also fixes drift. Something edited by hand at 3am gets reverted on the next '
        'reconcile, and you find out, instead of discovering months later that prod does not '
        'match the manifests.'),
  ('h2', 'Kustomize: patch, do not template'),
  ('p', 'Kustomize keeps one real set of manifests and expresses each environment as a patch over '
        'it. The base is valid YAML you can apply directly, which makes it reviewable.'),
  ('code', '''# base/kustomization.yaml
resources:
  - deployment.yaml
  - service.yaml

# overlays/prod/kustomization.yaml
resources:
  - ../../base
replicas:
  - name: my-app
    count: 6
patches:
  - path: resources.yaml       # prod gets bigger requests
    target: { kind: Deployment, name: my-app }
images:
  - name: my-app
    newTag: v1.4.2'''),
  ('code', '''# always read the output before trusting it
kubectl kustomize overlays/prod | less
kubectl diff -k overlays/prod                  # what would change, against the live cluster'''),
  ('note', '<b><code>kubectl diff -k</code> is the most underused command in this area.</b> It '
           'shows exactly what a merge would do to the live cluster, which turns "I think this is '
           'safe" into something you can paste into a pull request.'),
  ('h2', 'Helm or Kustomize: pick by failure mode'),
  ('ul', ['<strong>Helm</strong> when you are consuming somebody else&rsquo;s software. You want their '
          'upgrade path, their values schema, their defaults.',
          '<strong>Kustomize</strong> when the manifests are yours. Patches stay readable; '
          'templated YAML stops being YAML and starts being a string-concatenation program.',
          '<strong>Both</strong> is normal and fine: render the upstream chart, then patch the '
          'result.']),
  ('h2', 'App-of-apps, and why bootstrap order matters'),
  ('p', 'Put one root application in Git that points at everything else. Recovering the cluster '
        'becomes: install the reconciler, apply the root, wait.'),
  ('code', '''# the only thing you ever apply by hand
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: root, namespace: argocd }
spec:
  source:
    repoURL: https://github.com/you/platform
    path: apps                  # a directory of Application manifests
  destination: { server: https://kubernetes.default.svc }
  syncPolicy:
    automated: { prune: true, selfHeal: true }'''),
  ('gotcha', '<b>Turn on <code>prune</code> deliberately and late.</b> Without it, deleting a file '
             'from Git leaves the object running forever, and your repo quietly stops describing '
             'reality. With it, a bad path or a mistaken refactor can delete real workloads. '
             'Enable it once you trust the repo layout, not on day one.'),
  ('p', 'Order is the other bootstrap trap: CRDs must exist before the resources that use them, '
        'and namespaces before the things inside them. Sync waves — or Flux dependencies — exist '
        'for exactly this, and you will need them the first time you rebuild from scratch.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Run <code>kubectl diff -k</code> against production once. Whatever it prints is your '
          'current drift.',
          'Move one service to an overlay structure and delete its duplicated YAML.',
          'Write down the bootstrap order for your cluster. If you cannot, that is the finding.']),
 ],
},

# ---------------------------------------------------------------- operate
{
 'node': 'control-plane', 'slug': 'control-plane-and-etcd',
 'title': 'Control plane components and etcd', 'minutes': 11, 'added': D,
 'dek': 'What each component owns, plus a real backup and restore of etcd on a cluster you '
        'can afford to destroy.',
 'body': [
  ('p', 'Four processes make the control plane, and knowing which one owns a decision is the '
        'difference between fixing a cluster and restarting things hopefully.'),
  ('h2', 'Who owns what'),
  ('ul', ['<strong>etcd</strong> &mdash; the only stateful thing. If it is gone, the cluster is gone.',
          '<strong>kube-apiserver</strong> &mdash; the only process that talks to etcd. Everything '
          'else talks to it. Stateless, so you can run several.',
          '<strong>kube-scheduler</strong> &mdash; decides which node a pod goes to, then writes '
          'that decision down. It does not start anything.',
          '<strong>kube-controller-manager</strong> &mdash; the built-in reconcile loops: '
          'Deployments, ReplicaSets, node lifecycle, endpoints.',
          '<strong>kubelet</strong> &mdash; on every node, the only thing that actually starts '
          'containers.']),
  ('p', 'A useful consequence: if the scheduler is down, running pods are completely unaffected '
        'and new pods sit in <code>Pending</code>. If the API server is down, running pods keep '
        'running and nothing can be changed or observed. Neither is an outage of your '
        'application &mdash; which is a surprise to most people the first time.'),
  ('h2', 'Follow one apply through the system'),
  ('ol', ['<code>kubectl</code> POSTs to the API server, which authenticates, authorises via '
          'RBAC, runs admission, validates, and writes to etcd.',
          'The Deployment controller sees the new object and creates a ReplicaSet.',
          'The ReplicaSet controller creates Pod objects with no <code>nodeName</code>.',
          'The scheduler notices unassigned pods and writes a binding.',
          'The kubelet on that node sees a pod assigned to it, pulls the image and starts '
          'containers through the CRI.',
          'The kubelet reports status back; the endpoint controller adds the pod to Services '
          'once it is ready.']),
  ('note', 'Nothing in that chain is a direct call to the next step. Each stage watches the API '
           'server and acts. That is why the system survives any one piece being briefly absent, '
           'and why &ldquo;nothing happened and there is no error&rdquo; is a normal failure '
           'mode &mdash; some watcher is not running.'),
  ('h2', 'Static pods: the bootstrap trick'),
  ('p', 'On a kubeadm cluster the control plane runs as pods &mdash; but something has to start '
        'them before the control plane exists. The kubelet reads manifests straight off disk:'),
  ('code', 'ls /etc/kubernetes/manifests/\n'
           '# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml\n\n'
           '# moving a file out of this directory stops that component, immediately\n'
           'sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/\n'
           'kubectl get pods -n kube-system | grep scheduler    # gone\n'
           'sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/    # back'),
  ('p', 'That is also the repair path when the API server will not start: you edit the manifest '
        'on disk, because you cannot use the API to fix the API.'),
  ('h2', 'Back up etcd, then actually restore it'),
  ('code', 'ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db \\\n'
           '  --endpoints=https://127.0.0.1:2379 \\\n'
           '  --cacert=/etc/kubernetes/pki/etcd/ca.crt \\\n'
           '  --cert=/etc/kubernetes/pki/etcd/server.crt \\\n'
           '  --key=/etc/kubernetes/pki/etcd/server.key\n\n'
           'ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-2026-10-08.db --write-out=table'),
  ('p', 'The restore is the part worth rehearsing, because it is not symmetrical with the backup. '
        'You stop the control plane, restore into a <em>new</em> data directory, point etcd at it, '
        'and start everything again:'),
  ('code', 'sudo mv /etc/kubernetes/manifests/*.yaml /tmp/manifests-backup/   # stop control plane\n\n'
           'sudo ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-2026-10-08.db \\\n'
           '  --data-dir=/var/lib/etcd-restored\n\n'
           'sudo vim /etc/kubernetes/manifests/etcd.yaml   # point hostPath at /var/lib/etcd-restored\n'
           'sudo mv /tmp/manifests-backup/*.yaml /etc/kubernetes/manifests/'),
  ('gotcha', '<b>A snapshot you have never restored is not a backup.</b> Two mistakes show up '
             'every time: restoring into the existing data directory instead of a new one, and '
             'forgetting to update the <code>hostPath</code> in <code>etcd.yaml</code> &mdash; so '
             'etcd starts on the old data and the restore appears to have done nothing. Do it '
             'twice on a throwaway cluster.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Build a <code>kind</code> or kubeadm cluster you do not care about and destroy etcd '
          'deliberately.',
          'Stop the scheduler for two minutes and watch what breaks &mdash; less than you expect.',
          'Write the restore procedure down as commands, not prose, and keep it somewhere you can '
          'reach without the cluster.']),
 ],
},
{
 'node': 'rbac-tenancy', 'slug': 'rbac-and-multi-tenancy',
 'title': 'RBAC and multi-tenancy', 'minutes': 10, 'added': D,
 'dek': 'Roles that are actually least-privilege, and the three places tenancy leaks anyway.',
 'body': [
  ('p', 'RBAC is four object types and one rule: permissions are purely additive, and there is no '
        'deny. What a subject can do is the union of every binding that mentions it, which means '
        'you can never fix an over-permissive grant by adding a narrower one.'),
  ('h2', 'Four objects, two scopes'),
  ('ul', ['<strong>Role</strong> &mdash; permissions, inside one namespace.',
          '<strong>ClusterRole</strong> &mdash; permissions, cluster-wide or reusable.',
          '<strong>RoleBinding</strong> &mdash; grants a Role <em>or a ClusterRole</em> inside one '
          'namespace.',
          '<strong>ClusterRoleBinding</strong> &mdash; grants a ClusterRole everywhere.']),
  ('note', 'The combination people miss: a <strong>RoleBinding referencing a ClusterRole</strong>. '
           'That is how you define &ldquo;developer&rdquo; once and grant it in thirty namespaces '
           'without thirty copies of the rules. The single most useful pattern in RBAC.'),
  ('h2', 'Ask the API rather than reading YAML'),
  ('code', 'kubectl auth can-i --list --as=system:serviceaccount:team-a:deployer -n team-a\n'
           'kubectl auth can-i delete pods --as=jane -n prod\n'
           "kubectl auth can-i '*' '*' --as=system:serviceaccount:team-a:deployer   # the scary one"),
  ('p', 'Reviewing bindings by eye does not work at any real scale, because the answer depends on '
        'role aggregation and on bindings in other namespaces. <code>can-i --list</code> gives '
        'you the effective answer, which is the only one that matters.'),
  ('h2', 'The escalation paths that are not obvious'),
  ('ul', ['<code>create pods</code> in a namespace means you can mount any Secret in that '
          'namespace and run as any ServiceAccount in it. It is effectively read access to every '
          'credential there.',
          '<code>create pods/exec</code> is a shell in a running container, bypassing whatever '
          'the image entrypoint was.',
          '<code>escalate</code> or <code>bind</code> on roles lets a subject grant itself '
          'permissions it does not have. RBAC normally prevents privilege escalation; these verbs '
          'are the exemption.',
          '<code>get secrets</code> cluster-wide is usually equivalent to cluster-admin in '
          'practice, because one of those secrets is a token for something that is.']),
  ('gotcha', '<b>Namespaces are not a security boundary on their own.</b> They scope names and '
             'RBAC, and nothing else. By default a pod in one namespace can reach a pod in '
             'another over the network, both can exhaust the same node, and both see the same '
             'cluster-scoped objects. Real tenancy needs network policy, quotas and admission '
             'control on top.'),
  ('h2', 'Three leaks to close'),
  ('ol', ['<strong>Network.</strong> Without NetworkPolicy, every pod can reach every pod. A '
          'default-deny policy per namespace is the first real wall.',
          '<strong>Resources.</strong> Without a ResourceQuota and LimitRange, one tenant can '
          'take a whole node. Noisy-neighbour problems are tenancy problems.',
          '<strong>Node and kernel.</strong> Pods share a kernel. A privileged container, a '
          'hostPath mount or <code>hostNetwork</code> escapes the namespace entirely &mdash; '
          'which is what Pod Security Admission is for.']),
  ('code', '# the baseline worth having in every tenant namespace\n'
           'apiVersion: v1\n'
           'kind: Namespace\n'
           'metadata:\n'
           '  name: team-a\n'
           '  labels:\n'
           '    pod-security.kubernetes.io/enforce: restricted\n'
           '    pod-security.kubernetes.io/warn: restricted'),
  ('h2', 'Default ServiceAccount tokens'),
  ('p', 'Every pod gets a ServiceAccount token mounted unless you say otherwise. Most workloads '
        'never call the API, so that token is pure downside &mdash; it is the first thing anything '
        'inside a compromised container goes looking for.'),
  ('code', 'spec:\n'
           '  automountServiceAccountToken: false     # on the pod, or on the ServiceAccount'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Run <code>can-i --list</code> for your most-used ServiceAccount. Expect a surprise.',
          'Find every binding of <code>cluster-admin</code> and justify each one out loud.',
          'Turn off token automounting on one workload that does not need it, and watch nothing '
          'break.']),
 ],
},
{
 'node': 'troubleshoot', 'slug': 'troubleshooting-under-time-pressure',
 'title': 'Troubleshooting under time pressure', 'minutes': 9, 'added': D,
 'dek': 'A fixed order of operations for a broken cluster, so you stop guessing when it '
        'matters most.',
 'body': [
  ('p', 'Under pressure people debug by hunch, and hunches are biased towards whatever broke last '
        'time. A fixed order is slightly slower on the occasions you guess right, and '
        'dramatically faster on average.'),
  ('h2', 'The order'),
  ('ol', ['<strong>Is the pod scheduled?</strong> <code>Pending</code> is a scheduler problem, '
          'never an application problem.',
          '<strong>Did the image arrive?</strong> <code>ImagePullBackOff</code> is registry, '
          'credentials or a typo.',
          '<strong>Did the process start?</strong> <code>CrashLoopBackOff</code> means it ran and '
          'exited &mdash; read the <em>previous</em> logs.',
          '<strong>Is it ready?</strong> Running but receiving no traffic is a probe or a selector.',
          '<strong>Can it reach what it needs?</strong> Now, and only now, is it networking.']),
  ('p', 'Each step rules out a whole class of cause. Skipping to step five is how an afternoon '
        'disappears into packet captures for what turns out to be a failing readiness probe.'),
  ('h2', 'Events before logs, always'),
  ('code', 'kubectl get events -n prod --sort-by=.lastTimestamp | tail -30\n'
           "kubectl describe pod my-app-xyz | sed -n '/Events:/,$p'"),
  ('p', 'Events are where the scheduler and kubelet explain themselves: '
        '<code>Insufficient cpu</code>, <code>node(s) had untolerated taint</code>, '
        '<code>FailedMount</code>, <code>Liveness probe failed</code>. They answer &ldquo;why is '
        'this not running&rdquo; in a way logs never do, because the application never got far '
        'enough to log.'),
  ('gotcha', '<b>Events expire, by default after an hour.</b> An empty event list on a pod that '
             'has been broken since last night means nothing at all. Check the pod age against '
             'the retention window before concluding there is nothing there.'),
  ('h2', 'The previous container is the one that failed'),
  ('code', 'kubectl logs my-app-xyz --previous             # the instance that crashed\n'
           'kubectl logs my-app-xyz -c sidecar --previous  # and the right container\n'
           "kubectl get pod my-app-xyz \\\n"
           "  -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'"),
  ('p', 'In a crash loop, <code>kubectl logs</code> without <code>--previous</code> shows the '
        'fresh container that has not failed yet, which is usually empty. That is the most common '
        'reason people believe an application logs nothing on failure.'),
  ('p', 'Exit codes are worth memorising. <strong>137</strong> is SIGKILL &mdash; almost always an '
        'OOM kill or a failed liveness probe. <strong>143</strong> is SIGTERM, a normal shutdown. '
        '<strong>1</strong> or <strong>2</strong> is your application failing on its own terms, so '
        'read the logs.'),
  ('h2', 'Node NotReady: the first five commands'),
  ('code', 'kubectl get nodes -o wide\n'
           "kubectl describe node bad-node | sed -n '/Conditions:/,/Addresses:/p'\n"
           '# then on the node itself\n'
           'systemctl status kubelet\n'
           'journalctl -u kubelet -n 100 --no-pager\n'
           'df -h /var/lib/kubelet && free -m'),
  ('p', 'Node conditions name the problem directly: <code>DiskPressure</code>, '
        '<code>MemoryPressure</code>, <code>KubeletNotReady</code>. A full disk on '
        '<code>/var/lib/kubelet</code> is the most common cause of a node going NotReady and '
        'having its pods evicted, and it is invisible from the cluster side until you look.'),
  ('h2', 'Debugging a container with no shell'),
  ('code', '# attach a debug container to a running pod, sharing its namespaces\n'
           'kubectl debug -it my-app-xyz --image=nicolaka/netshoot --target=app\n\n'
           '# a copy of the pod with the command replaced, when it crashes too fast to exec into\n'
           'kubectl debug my-app-xyz -it --copy-to=debug-pod --container=app -- sh'),
  ('p', 'Distroless and scratch images have no shell on purpose, which is good for security and '
        'awkward at 2am. <code>kubectl debug</code> solves it without rebuilding the image or '
        'weakening it.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Write the five-step order somewhere you will see it during an incident.',
          'Practise <code>kubectl debug</code> once, before you need it.',
          'Check disk on your nodes now. It is the cheapest outage to prevent.']),
 ],
},

# ---------------------------------------------------------------- networking
{
 'node': 'pod-networking', 'slug': 'pod-networking-from-first-principles',
 'title': 'Pod networking from first principles', 'minutes': 12, 'added': D,
 'dek': 'Follow a packet from one pod to another across nodes, then do it again with the CNI '
        'removed so you can see what it was doing for you.',
 'body': [
  ('p', 'Kubernetes networking has exactly three rules. Everything else is an implementation '
        'detail of satisfying them:'),
  ('ol', ['Every pod gets its own IP address.',
          'Pods can reach each other at those addresses, without NAT.',
          'Agents on a node can reach all pods on that node.']),
  ('p', 'That is the whole contract. It feels complicated because nothing in Linux provides it, '
        'so a CNI plugin has to build it on every node, and the plugins do it differently.'),
  ('h2', 'Inside a node: veth pairs'),
  ('p', 'A pod is a network namespace. To give it connectivity the plugin creates a virtual '
        'ethernet pair &mdash; a cable with two ends &mdash; puts one end inside the namespace as '
        '<code>eth0</code>, and leaves the other on the host.'),
  ('code', "# find the pod's interface index from inside the pod\n"
           'kubectl exec my-pod -- cat /sys/class/net/eth0/iflink\n'
           '# then match that index on the node\n'
           'ip link | grep "^<index>:"\n\n'
           '# the host side of every pod on this node\n'
           'ip -d link show type veth'),
  ('p', 'The pod routing table is deliberately almost empty: a default route pointing at the host '
        'side of the pair. Every real decision is made on the node, not in the pod.'),
  ('h2', 'Between nodes: overlay or routed'),
  ('ul', ['<strong>Overlay</strong> (VXLAN, Geneve) wraps the pod packet inside a node-to-node '
          'packet. Works on any network, costs you MTU and a little CPU.',
          '<strong>Routed</strong> (BGP, or a cloud route table) tells the underlying network '
          'where each node pod CIDR lives, so pod packets travel unmodified. Faster and easier to '
          'debug, but the network has to cooperate.']),
  ('gotcha', '<b>MTU is the silent killer in overlay mode.</b> VXLAN adds 50 bytes of headers. If '
             'the pod MTU is still 1500 on a 1500-byte underlay, large packets need fragmenting, '
             'and if ICMP is filtered anywhere you get the classic symptom: small requests work, '
             'TLS handshakes and large responses hang forever. Run '
             '<code>kubectl exec pod -- ip link show eth0</code> and expect 1450, not 1500.'),
  ('h2', 'Services are not processes'),
  ('p', 'A ClusterIP does not exist anywhere. No process listens on it. It is a rule on every node '
        'that rewrites the destination of outgoing packets to one of the backing pod IPs:'),
  ('code', '# iptables mode - the classic\n'
           'sudo iptables -t nat -L KUBE-SERVICES -n | grep my-svc\n\n'
           '# IPVS mode - a real load balancer table\n'
           'sudo ipvsadm -Ln\n\n'
           '# what the Service actually resolves to\n'
           'kubectl get endpointslices -l kubernetes.io/service-name=my-svc -o yaml'),
  ('p', 'The modes differ only in how that rewriting is implemented. <strong>iptables</strong> '
        'builds a chain per service and scales linearly, which starts hurting in the thousands. '
        '<strong>IPVS</strong> uses a kernel hash table and stays flat. <strong>eBPF</strong> '
        'replaces the chains with programs attached to the socket and the interface, and can skip '
        'much of the network stack for pods on the same node.'),
  ('h2', 'DNS is the usual suspect'),
  ('code', 'kubectl exec -it my-pod -- cat /etc/resolv.conf\n'
           '# nameserver 10.96.0.10\n'
           '# search team-a.svc.cluster.local svc.cluster.local cluster.local\n'
           '# options ndots:5'),
  ('p', '<code>ndots:5</code> means any name with fewer than five dots is tried against every '
        'search domain first. A lookup of <code>api.example.com</code> &mdash; two dots &mdash; '
        'generates four failing queries before the correct one. Harmless until DNS is under load, '
        'at which point it is four times the load you think you have. A trailing dot '
        '(<code>api.example.com.</code>) skips the search list entirely.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Find the veth pair for one of your pods, on the node. Two commands, and the model '
          'stops being abstract.',
          'Check your pod MTU. If it is 1500 on an overlay, you have a latent bug.',
          'Dump the iptables NAT table or run <code>ipvsadm -Ln</code> once, so a Service stops '
          'being magic.']),
 ],
},
{
 'node': 'network-policy', 'slug': 'network-policy-you-can-debug',
 'title': 'Network policy that someone can debug', 'minutes': 10, 'added': D,
 'dek': 'Default-deny without taking production down, and proving the policy does what you '
        'claimed it does.',
 'body': [
  ('p', 'An empty cluster is a flat network: every pod can reach every other pod, in every '
        'namespace. NetworkPolicy is how you stop that, and the reason most teams never finish '
        'rolling it out is that the first attempt breaks something at 9am.'),
  ('h2', 'The model, which is unlike a firewall'),
  ('ul', ['Policies are <strong>allow-only</strong>. There is no deny rule.',
          'A pod with <strong>no policy</strong> selecting it allows everything.',
          'A pod with <strong>any</strong> policy selecting it denies everything not explicitly '
          'allowed, <em>for that direction</em>.',
          'Ingress and egress are independent. A policy with only ingress rules leaves egress '
          'wide open.']),
  ('note', 'That third rule is the whole trick. You do not write a deny &mdash; you make a pod '
           'selected by <em>some</em> policy, which flips it to default-deny, and then add back '
           'what it genuinely needs.'),
  ('h2', 'Default-deny, and why it bites'),
  ('code', 'apiVersion: networking.k8s.io/v1\n'
           'kind: NetworkPolicy\n'
           'metadata:\n'
           '  name: default-deny-all\n'
           '  namespace: team-a\n'
           'spec:\n'
           '  podSelector: {}            # every pod in the namespace\n'
           '  policyTypes: [Ingress, Egress]'),
  ('gotcha', '<b>Apply that and DNS stops working.</b> Egress deny includes UDP 53 to CoreDNS in '
             '<code>kube-system</code>, so every pod in the namespace starts failing name '
             'resolution &mdash; which surfaces as application timeouts, not as a network error, '
             'and sends people looking in entirely the wrong place. Always pair default-deny with '
             'a DNS allowance in the same commit.'),
  ('code', 'apiVersion: networking.k8s.io/v1\n'
           'kind: NetworkPolicy\n'
           'metadata:\n'
           '  name: allow-dns\n'
           '  namespace: team-a\n'
           'spec:\n'
           '  podSelector: {}\n'
           '  policyTypes: [Egress]\n'
           '  egress:\n'
           '    - to:\n'
           '        - namespaceSelector:\n'
           '            matchLabels:\n'
           '              kubernetes.io/metadata.name: kube-system\n'
           '          podSelector:\n'
           '            matchLabels:\n'
           '              k8s-app: kube-dns\n'
           '      ports:\n'
           '        - { protocol: UDP, port: 53 }\n'
           '        - { protocol: TCP, port: 53 }'),
  ('h2', 'The selector trap that silently widens a rule'),
  ('p', 'In a single <code>to</code> or <code>from</code> block, listing '
        '<code>namespaceSelector</code> and <code>podSelector</code> as two array items is an OR. '
        'Putting them under one item, as above, is an AND. The YAML difference is a single dash:'),
  ('code', '# AND - pods matching app=api, in namespaces matching team=a\n'
           'from:\n'
           '  - namespaceSelector: { matchLabels: { team: a } }\n'
           '    podSelector: { matchLabels: { app: api } }\n\n'
           '# OR - every pod in those namespaces, PLUS every app=api pod anywhere\n'
           'from:\n'
           '  - namespaceSelector: { matchLabels: { team: a } }\n'
           '  - podSelector: { matchLabels: { app: api } }'),
  ('p', 'The second form is almost never what anyone means, and it reviews as correct. It is the '
        'most common real defect in policy I have seen.'),
  ('h2', 'Roll it out without an incident'),
  ('ol', ['Start in a <strong>non-production namespace</strong> and get DNS right there first.',
          'Write the <strong>allow</strong> policies before the deny, and apply them first. They '
          'do nothing on their own, because nothing is denied yet.',
          'Apply default-deny <strong>per namespace</strong>, never cluster-wide in one go.',
          'Watch for drops rather than waiting for complaints.']),
  ('h2', 'Proving it, instead of hoping'),
  ('code', '# the direct test, from a pod that should be refused\n'
           'kubectl run probe --rm -it --image=nicolaka/netshoot -n team-b -- \\\n'
           '  curl -m 3 http://api.team-a.svc.cluster.local\n\n'
           '# with Cilium: watch the verdicts live\n'
           'cilium hubble observe --verdict DROPPED --namespace team-a\n\n'
           '# with Cilium: ask, rather than test\n'
           'cilium connectivity test'),
  ('p', 'Plain upstream NetworkPolicy has no observability at all &mdash; a dropped packet is '
        'just a timeout. That absence is the strongest practical argument for Cilium or Calico '
        'over a minimal CNI: not the policy features, but being able to see the drop and name the '
        'rule that caused it.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Apply default-deny plus DNS to one non-production namespace this week.',
          'Grep your existing policies for the OR-versus-AND mistake. Check every '
          '<code>from</code> block with two dashes.',
          'Pick a CNI that can show you drops before you need to debug one.']),
 ],
},
{
 'node': 'gateway-mesh', 'slug': 'gateway-api-and-the-mesh-decision',
 'title': 'Gateway API and the mesh decision', 'minutes': 11, 'added': D,
 'dek': 'Ingress to Gateway API route by route, and an honest list of what a service mesh '
        'costs you.',
 'body': [
  ('p', 'Ingress did one job and did it with annotations. Gateway API replaces it with real typed '
        'resources and, more importantly, a split of responsibility that matches how teams '
        'actually work.'),
  ('h2', 'Why the split matters more than the schema'),
  ('ul', ['<strong>GatewayClass</strong> &mdash; the implementation. Installed once, by whoever '
          'runs the platform.',
          '<strong>Gateway</strong> &mdash; the listener: ports, protocols, TLS. Owned by the '
          'platform team.',
          '<strong>HTTPRoute</strong> &mdash; hostnames, paths, backends, weights. Owned by the '
          'application team, in their own namespace.']),
  ('p', 'With Ingress, a developer needing a header-based rule had to edit an annotation blob '
        'that only the controller understood, usually in a shared object. With Gateway API they '
        'write an HTTPRoute in their namespace and attach it to a Gateway they are permitted to '
        'use. The RBAC boundary finally lines up with the ownership boundary.'),
  ('h2', 'A route, and a canary'),
  ('code', 'apiVersion: gateway.networking.k8s.io/v1\n'
           'kind: HTTPRoute\n'
           'metadata:\n'
           '  name: api\n'
           '  namespace: team-a\n'
           'spec:\n'
           '  parentRefs:\n'
           '    - name: public-gateway\n'
           '      namespace: infra\n'
           '  hostnames: ["api.example.com"]\n'
           '  rules:\n'
           '    - matches:\n'
           '        - path: { type: PathPrefix, value: /v2 }\n'
           '      backendRefs:\n'
           '        - { name: api-v2, port: 8080, weight: 90 }\n'
           '        - { name: api-v2-canary, port: 8080, weight: 10 }'),
  ('p', 'Weighted backends are in the core specification, not an annotation and not a separate '
        'product. That single feature removes the most common reason teams installed a mesh.'),
  ('h2', 'Migrating without a flag day'),
  ('ol', ['Install a Gateway API implementation alongside your existing ingress controller. They '
          'coexist happily.',
          'Create the Gateway with a <strong>different hostname</strong> &mdash; '
          '<code>new.api.example.com</code> &mdash; and port it one route at a time.',
          'Shift traffic at DNS, with a low TTL, once the new path is proven.',
          'Delete the Ingress objects last, and only after a week of quiet.']),
  ('note', 'Keep <code>ReferenceGrant</code> in mind: a route in one namespace pointing at a '
           'Service in another is <em>denied by default</em>. The target namespace has to publish '
           'a ReferenceGrant permitting it. This is a feature &mdash; it stops a team routing '
           'traffic to someone else’s service &mdash; and it is the most common reason a '
           'migrated route silently returns 404.'),
  ('h2', 'When a service mesh is the wrong answer'),
  ('p', 'A mesh gives you mutual TLS everywhere, uniform retries and timeouts, L7 authorisation, '
        'and per-call telemetry you did not have to instrument. Those are real. So is the bill:'),
  ('ul', ['<strong>A sidecar per pod</strong>, or an eBPF agent per node. Either way, memory and '
          'CPU across your whole fleet &mdash; often 10&ndash;15% before you have shipped '
          'anything.',
          '<strong>Two more hops in every request path</strong>, and two more places a request '
          'can be dropped.',
          '<strong>A second control plane</strong> to upgrade, certificate-rotate and debug, with '
          'its own failure modes that look like application failures.',
          '<strong>Startup ordering</strong> &mdash; the classic sidecar race where your app '
          'starts before the proxy is ready and its first calls fail.']),
  ('p', 'A reasonable sequence: Gateway API first, because you need an ingress anyway. Then '
        'NetworkPolicy, which covers most of what people want mTLS for internally. Reach for a '
        'mesh when you have a concrete requirement &mdash; mTLS for compliance, retries you '
        'cannot put in clients, L7 authorisation between services &mdash; not because the '
        'architecture diagram looks incomplete without one.'),
  ('p', 'If you do want mTLS and nothing else, an eBPF CNI can give you transparent node-to-node '
        'encryption with no sidecars at all. That is a much smaller commitment than a full mesh '
        'and it covers the single most common compliance ask.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Install a Gateway API implementation next to your ingress controller and port one '
          'route.',
          'Write down the specific requirement that would justify a mesh. If you cannot name one, '
          'you have your answer.',
          'Check whether your CNI can do transparent encryption before pricing a mesh.']),
 ],
},

# ---------------------------------------------------------------- security
{
 'node': 'admission-policy', 'slug': 'admission-control-and-policy-as-code',
 'title': 'Admission control and policy as code', 'minutes': 10, 'added': D,
 'dek': 'Pod Security Admission first, then a policy engine for the rules PSA cannot express '
        'and a webhook only when nothing else will do.',
 'body': [
  ('p', 'Admission control is the last point at which you can say no. It runs after '
        'authentication and authorisation, after the object has been validated, and before '
        'anything is written to etcd &mdash; so a rejection means the bad object never existed.'),
  ('h2', 'Three tiers, in order of how much they cost you'),
  ('ol', ['<strong>Pod Security Admission</strong> &mdash; built in, three labels, no components '
          'to run. Covers the dangerous pod fields.',
          '<strong>A policy engine</strong> (Kyverno, Gatekeeper) &mdash; declarative rules for '
          'everything else, including mutation and cross-object checks.',
          '<strong>A custom webhook</strong> &mdash; arbitrary code, maximum power, and now you '
          'own an availability problem.']),
  ('p', 'Most teams reach straight for tier two and skip tier one, then write forty policies '
        'reimplementing what three labels would have done.'),
  ('h2', 'Pod Security Admission, which is free'),
  ('code', 'apiVersion: v1\n'
           'kind: Namespace\n'
           'metadata:\n'
           '  name: team-a\n'
           '  labels:\n'
           '    pod-security.kubernetes.io/enforce: baseline     # reject the worst\n'
           '    pod-security.kubernetes.io/enforce-version: v1.31\n'
           '    pod-security.kubernetes.io/audit: restricted     # log what would fail\n'
           '    pod-security.kubernetes.io/warn: restricted      # warn the applier'),
  ('note', 'The sequence that works: set <code>warn</code> and <code>audit</code> to '
           '<code>restricted</code> while <code>enforce</code> stays at <code>baseline</code>. '
           'You get the full list of what would break, in warnings and the audit log, without '
           'breaking it. Tighten <code>enforce</code> once that list is empty.'),
  ('p', '<code>baseline</code> blocks privileged containers, host namespaces, hostPath and '
        'dangerous capabilities. <code>restricted</code> additionally requires non-root, dropping '
        'all capabilities and a seccomp profile. The gap between them is where almost every real '
        'application argument happens.'),
  ('h2', 'Policy engines: validate, then mutate, then generate'),
  ('code', 'apiVersion: kyverno.io/v1\n'
           'kind: ClusterPolicy\n'
           'metadata:\n'
           '  name: require-requests\n'
           'spec:\n'
           '  validationFailureAction: Audit      # start here, never Enforce\n'
           '  rules:\n'
           '    - name: resources-set\n'
           '      match:\n'
           '        any:\n'
           '          - resources: { kinds: [Pod] }\n'
           '      validate:\n'
           '        message: "every container needs cpu and memory requests"\n'
           '        pattern:\n'
           '          spec:\n'
           '            containers:\n'
           '              - resources:\n'
           '                  requests:\n'
           '                    memory: "?*"\n'
           '                    cpu: "?*"'),
  ('p', 'The underrated half is mutation and generation: default a security context rather than '
        'rejecting pods that lack one, or generate a default-deny NetworkPolicy into every new '
        'namespace automatically. A policy that fixes the problem produces far less friction than '
        'one that lectures about it.'),
  ('h2', 'The failure mode to design for'),
  ('gotcha', '<b>A validating webhook with <code>failurePolicy: Fail</code> that becomes '
             'unavailable will block every matching API write in the cluster.</b> If its scope '
             'includes namespaces, and the webhook pod needs a namespace, you have a deadlock that '
             'survives restarts. This has taken down real clusters. Always exclude '
             '<code>kube-system</code> and your policy engine’s own namespace, and think '
             'hard before <code>Fail</code>.'),
  ('code', '# the exclusion that saves you\n'
           'namespaceSelector:\n'
           '  matchExpressions:\n'
           '    - key: kubernetes.io/metadata.name\n'
           '      operator: NotIn\n'
           '      values: [kube-system, kyverno]'),
  ('h2', 'Policy that people do not route around'),
  ('ul', ['<strong>Audit before enforce</strong>, always. Ship the rule in audit mode, read what '
          'it would have blocked, then decide.',
          '<strong>Error messages with the fix in them.</strong> &ldquo;policy violation&rdquo; '
          'gets you a ticket; &ldquo;add resources.requests.memory, see &lt;link&gt;&rdquo; gets '
          'you a fixed manifest.',
          '<strong>Exceptions as objects, with expiry.</strong> A documented, time-limited '
          'exception beats a policy quietly weakened for everyone.',
          '<strong>Test in CI.</strong> Both engines can evaluate policies against manifests '
          'without a cluster, so a developer finds out in their pull request, not at deploy.']),
  ('h2', 'What to actually do with this'),
  ('ul', ['Add PSA labels in warn mode to every namespace today. It costs nothing and breaks '
          'nothing.',
          'Read the warnings for a week before enforcing anything.',
          'Check the <code>failurePolicy</code> and namespace exclusions on every webhook already '
          'in your cluster.']),
 ],
},
{
 'node': 'supply-chain', 'slug': 'supply-chain-and-image-provenance',
 'title': 'Supply chain and image provenance', 'minutes': 9, 'added': D,
 'dek': 'Signing, verifying, and actually failing closed when verification fails &mdash; '
        'which is the only part that matters.',
 'body': [
  ('p', 'Supply-chain security has a peculiar failure mode: almost everyone implements the '
        'signing half and stops. Signatures nobody verifies are a filing system, not a control.'),
  ('h2', 'Four separate questions'),
  ('ul', ['<strong>Integrity</strong> &mdash; is this the same bytes that were built? Digests.',
          '<strong>Authenticity</strong> &mdash; did we build it? Signatures.',
          '<strong>Provenance</strong> &mdash; from which commit, by which pipeline? Attestations.',
          '<strong>Composition</strong> &mdash; what is inside it? An SBOM.']),
  ('p', 'They are commonly bundled as one topic and they are not. You can have a signed image '
        'full of known-vulnerable packages, and an accurate SBOM for an image nobody can prove '
        'you built.'),
  ('h2', 'Tags are mutable. Digests are not.'),
  ('code', '# this can point somewhere else tomorrow\n'
           'image: ghcr.io/you/api:v1.4.2\n\n'
           '# this cannot\n'
           'image: ghcr.io/you/api@sha256:3f1b...c90a\n\n'
           '# what is that tag right now?\n'
           'crane digest ghcr.io/you/api:v1.4.2'),
  ('p', 'A tag is a mutable pointer. <code>v1.4.2</code> can be moved, and '
        '<code>imagePullPolicy: IfNotPresent</code> means different nodes may be running '
        'different bytes under the same tag with no sign of it. Deploying by digest removes a '
        'whole class of "works on one node" mystery, and it is what GitOps tooling should write '
        'for you.'),
  ('h2', 'Sign in the pipeline, verify at admission'),
  ('code', '# in CI, keyless: the identity is the workflow, not a key you have to store\n'
           'cosign sign --yes ghcr.io/you/api@sha256:3f1b...c90a\n\n'
           '# attach provenance and an SBOM as attestations\n'
           'syft ghcr.io/you/api@sha256:3f1b...c90a -o spdx-json > sbom.json\n'
           'cosign attest --yes --predicate sbom.json \\\n'
           '  --type spdxjson ghcr.io/you/api@sha256:3f1b...c90a'),
  ('p', 'Keyless signing is the part worth adopting deliberately. Instead of a private key you '
        'have to store and rotate, the signature is bound to an OIDC identity &mdash; the '
        'specific GitHub Actions workflow in the specific repository. There is no key to leak, '
        'and the thing you verify is "built by that workflow", which is what you actually wanted '
        'to know.'),
  ('code', 'apiVersion: kyverno.io/v1\n'
           'kind: ClusterPolicy\n'
           'metadata:\n'
           '  name: verify-images\n'
           'spec:\n'
           '  validationFailureAction: Enforce      # the whole point\n'
           '  rules:\n'
           '    - name: signed-by-our-workflow\n'
           '      match:\n'
           '        any:\n'
           '          - resources: { kinds: [Pod] }\n'
           '      verifyImages:\n'
           '        - imageReferences: ["ghcr.io/you/*"]\n'
           '          attestors:\n'
           '            - entries:\n'
           '                - keyless:\n'
           '                    subject: "https://github.com/you/api/.github/workflows/build.yml@refs/heads/main"\n'
           '                    issuer: "https://token.actions.githubusercontent.com"'),
  ('gotcha', '<b>Scope the <code>imageReferences</code> pattern carefully, and leave it in audit '
             'mode first.</b> A pattern of <code>*</code> will also catch your CNI, CoreDNS and '
             'metrics-server images, none of which are signed by your workflow &mdash; so '
             'enforcing it cluster-wide can prevent the cluster from recovering after a node '
             'reboot. Match your own registry prefix, and add exemptions for system namespaces '
             'before you switch to Enforce.'),
  ('h2', 'SBOMs are only useful if something reads them'),
  ('p', 'Generating an SBOM is one command. The value is entirely in what consumes it. A useful '
        'minimum: store the SBOM as an attestation next to the image, and run a scanner against '
        'your <em>running</em> images on a schedule &mdash; not just at build time. Vulnerability '
        'disclosures happen after you ship, which means the build-time scan that passed is not '
        'evidence about today.'),
  ('code', '# what is actually running, right now\n'
           'kubectl get pods -A -o jsonpath=\\\n'
           '  \'{range .items[*]}{range .status.containerStatuses[*]}{.imageID}{"\\n"}{end}{end}\' \\\n'
           '  | sort -u'),
  ('p', 'That list is the only inventory that matters, and it is usually shorter and stranger than '
        'anyone expects.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Pin one production workload to a digest and notice what else has to change.',
          'Add <code>cosign sign</code> to one pipeline this week; verification can come later.',
          'Switch verification on in audit mode and read what fails before enforcing.',
          'Scan running images on a schedule, not only at build.']),
 ],
},
{
 'node': 'runtime-detect', 'slug': 'runtime-detection-and-response',
 'title': 'Runtime detection and response', 'minutes': 9, 'added': D,
 'dek': 'Seeing a container do something it should not, and having a plan for the next ten '
        'minutes rather than inventing one live.',
 'body': [
  ('p', 'Everything up to this point is prevention. Runtime detection assumes prevention failed, '
        'which over a long enough period it will. The question is whether you would notice.'),
  ('h2', 'Where the signal comes from'),
  ('ul', ['<strong>Syscalls</strong> &mdash; eBPF or a kernel module watching what processes '
          'actually do. Falco and Tetragon live here. Highest fidelity, highest volume.',
          '<strong>The audit log</strong> &mdash; every request to the API server. The only '
          'record of who did what to the cluster.',
          '<strong>Network flows</strong> &mdash; who talked to whom. Hubble, or any flow log.',
          '<strong>Image and process inventory</strong> &mdash; what is running that was not '
          'running yesterday.']),
  ('h2', 'Rules worth having on day one'),
  ('p', 'Falco ships hundreds of rules and the default set is noisy enough that people turn it '
        'off. Start with a handful that are nearly always true positives:'),
  ('ul', ['A shell spawned inside a container that has no business running one.',
          'Writes below <code>/etc</code> or <code>/usr/bin</code> in a running container.',
          'A process reading <code>/var/run/secrets/kubernetes.io/serviceaccount/token</code> '
          'that is not your application.',
          'An outbound connection to an address outside your egress allowlist.',
          'Any attempt to mount <code>/var/run/docker.sock</code> or the container runtime socket.']),
  ('code', '- rule: Shell in a production container\n'
           '  desc: interactive shell started where none should exist\n'
           '  condition: >\n'
           '    spawned_process and container\n'
           '    and proc.name in (bash, sh, zsh, ash)\n'
           '    and k8s.ns.name startswith "prod-"\n'
           '  output: >\n'
           '    shell in container (user=%user.name container=%container.name\n'
           '    ns=%k8s.ns.name pod=%k8s.pod.name cmd=%proc.cmdline)\n'
           '  priority: WARNING'),
  ('note', 'Put the <strong>namespace and pod name</strong> in every output. A detection that '
           'tells you something happened but not where is an alert you cannot act on, and it '
           'trains people to ignore the channel it arrives in.'),
  ('h2', 'Your audit log is your only witness'),
  ('p', 'Syscall detection tells you what a container did. Only the API server audit log tells '
        'you what was done to the cluster &mdash; which token created that privileged pod, which '
        'identity read the Secret, what else that identity touched. It is off by default on many '
        'managed clusters and cannot be reconstructed afterwards.'),
  ('code', 'apiVersion: audit.k8s.io/v1\n'
           'kind: Policy\n'
           'rules:\n'
           '  - level: RequestResponse        # full bodies for the dangerous things\n'
           '    resources:\n'
           '      - group: ""\n'
           '        resources: ["secrets", "serviceaccounts/token"]\n'
           '      - group: "rbac.authorization.k8s.io"\n'
           '        resources: ["*"]\n'
           '  - level: Metadata               # who-did-what for everything else\n'
           '    omitStages: ["RequestReceived"]'),
  ('gotcha', '<b>Check whether your audit log is on, and where it goes, before you need it.</b> '
             'The first hour of an incident response is usually spent discovering that the '
             'evidence was never collected. Full <code>RequestResponse</code> on everything is '
             'too expensive; metadata on everything plus full bodies on secrets and RBAC is the '
             'ratio that works.'),
  ('h2', 'The next ten minutes, written down in advance'),
  ('ol', ['<strong>Contain, do not kill.</strong> Deleting the pod destroys the evidence and the '
          'Deployment recreates it anyway. Instead, cut it off.',
          '<strong>Isolate with a policy.</strong> Label the pod and apply a NetworkPolicy that '
          'selects that label and allows nothing.',
          '<strong>Detach it from its Service</strong> by changing a label the selector depends '
          'on &mdash; traffic stops, the pod keeps running, state is preserved.',
          '<strong>Capture</strong> process list, open sockets, environment and the audit trail '
          'for its ServiceAccount.',
          '<strong>Rotate</strong> every credential that pod could reach, which is every Secret '
          'in its namespace.',
          '<strong>Then</strong> delete it.']),
  ('code', '# isolate, keeping the process alive for inspection\n'
           'kubectl label pod suspect-xyz quarantine=true\n'
           'kubectl label pod suspect-xyz app-                 # drop it out of the Service\n\n'
           '# capture before anything else changes\n'
           'kubectl exec suspect-xyz -- ps auxf > /tmp/ps.txt\n'
           'kubectl exec suspect-xyz -- ss -tunap > /tmp/sockets.txt'),
  ('p', 'That label-removal trick is the most useful one in the list. It takes the pod out of '
        'rotation instantly, the ReplicaSet notices the shortfall and starts a healthy '
        'replacement, and the suspect pod is left running and idle for you to look at.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Deploy Falco with five rules rather than five hundred.',
          'Confirm today whether your audit log is enabled and where it lands.',
          'Write the six-step containment list somewhere findable, and rehearse the labelling '
          'once against a test pod.']),
 ],
},

# ---------------------------------------------------------------- inference
{
 'node': 'gpu-scheduling', 'slug': 'getting-a-gpu-into-a-pod',
 'title': 'Getting a GPU into a pod', 'minutes': 11, 'added': D,
 'dek': 'The device plugin model, drivers, and the difference between MIG and time-slicing '
        'when cost is the constraint.',
 'body': [
  ('p', 'No certification covers this, which is exactly why it is worth writing down. The '
        'mechanics are not hard; the failure modes are just unfamiliar, and every layer fails '
        'silently in its own way.'),
  ('h2', 'GPUs are not like CPU and memory'),
  ('p', 'CPU and memory are compressible, divisible, and known to the kubelet natively. A GPU is '
        'an <em>extended resource</em>: an opaque integer advertised by a device plugin, which '
        'cannot be fractional and cannot be overcommitted.'),
  ('code', 'resources:\n'
           '  limits:\n'
           '    nvidia.com/gpu: 1        # requests is implied and must equal limits\n\n'
           '# what the node claims to have\n'
           "kubectl get nodes -o custom-columns=\\\n"
           "  'NODE:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu'"),
  ('p', 'If that column is empty or zero, no pod requesting a GPU will ever schedule, and the '
        'only symptom is <code>Pending</code>. Nothing tells you the plugin is unhealthy; the '
        'resource simply does not exist.'),
  ('h2', 'Six layers, and the error is always in one of them'),
  ('ol', ['<strong>Hardware</strong> &mdash; the card is present. <code>lspci | grep -i nvidia</code>.',
          '<strong>Kernel driver</strong> &mdash; loaded and matching. <code>nvidia-smi</code> on '
          'the node.',
          '<strong>Container runtime</strong> &mdash; configured to inject devices, usually the '
          'NVIDIA container toolkit.',
          '<strong>Device plugin</strong> &mdash; a DaemonSet advertising the resource to the '
          'kubelet.',
          '<strong>Node labels</strong> &mdash; so you can target specific hardware.',
          '<strong>The pod spec</strong> &mdash; requesting the resource at all.']),
  ('code', '# the debugging order, top down\n'
           'kubectl get ds -n gpu-operator                        # plugin running?\n'
           'kubectl logs -n gpu-operator ds/nvidia-device-plugin-daemonset --tail=50\n'
           'kubectl describe node gpu-node-1 | grep -A5 Allocatable\n'
           'kubectl run smi --rm -it --restart=Never \\\n'
           '  --image=nvidia/cuda:12.4.0-base-ubuntu22.04 \\\n'
           "  --overrides='{\"spec\":{\"containers\":[{\"name\":\"smi\",\"image\":\"nvidia/cuda:12.4.0-base-ubuntu22.04\",\"command\":[\"nvidia-smi\"],\"resources\":{\"limits\":{\"nvidia.com/gpu\":1}}}]}}'"),
  ('note', 'Use the <strong>GPU Operator</strong> rather than assembling layers two to five by '
           'hand. It manages drivers, the toolkit, the device plugin, Node Feature Discovery and '
           'DCGM metrics as one unit, and it handles the thing that is genuinely painful manually: '
           'driver upgrades across a fleet without a cordon-and-reboot script of your own.'),
  ('h2', 'Sharing one GPU: two mechanisms, different guarantees'),
  ('ul', ['<strong>Time-slicing</strong> &mdash; the GPU context-switches between processes. '
          'Memory is <em>not</em> partitioned: every process sees the whole card and they can '
          'collectively exhaust it. No isolation, works on any GPU, zero reconfiguration.',
          '<strong>MIG</strong> (Multi-Instance GPU) &mdash; the hardware is partitioned into '
          'instances with dedicated memory, cache and compute. Real isolation, enforced by the '
          'card. Only on A100/H100-class hardware, and the partition layout is fixed until you '
          'reconfigure the device.']),
  ('gotcha', '<b>Time-slicing plus an untuned inference server is an OOM factory.</b> Frameworks '
             'like vLLM pre-allocate a large fraction of visible GPU memory by default. Two '
             'time-sliced replicas each try to reserve 90% of the same card, and the second one '
             'dies &mdash; or worse, both survive startup and one dies later under load. If you '
             'time-slice, you must cap memory per process in the application '
             '(<code>--gpu-memory-utilization</code> for vLLM) because Kubernetes cannot do it '
             'for you.'),
  ('code', '# time-slicing: four virtual GPUs from one physical card\n'
           'apiVersion: v1\n'
           'kind: ConfigMap\n'
           'metadata:\n'
           '  name: device-plugin-config\n'
           'data:\n'
           '  config.yaml: |\n'
           '    sharing:\n'
           '      timeSlicing:\n'
           '        resources:\n'
           '          - name: nvidia.com/gpu\n'
           '            replicas: 4\n\n'
           '# MIG: request a specific profile instead\n'
           '# resources:\n'
           '#   limits:\n'
           '#     nvidia.com/mig-1g.10gb: 1'),
  ('h2', 'Choosing between them'),
  ('ul', ['<strong>Many small, bursty, trusted workloads</strong> &mdash; notebooks, batch '
          'inference, development &mdash; time-slicing, with application memory caps.',
          '<strong>Multiple tenants, or anything with a latency target</strong> &mdash; MIG. A '
          'noisy neighbour on a time-sliced GPU can make your p99 unrecognisable.',
          '<strong>Training</strong> &mdash; neither. Give the job whole GPUs.']),
  ('h2', 'What to actually do with this'),
  ('ul', ['Run the six-layer check on a working GPU node so you know what healthy looks like.',
          'Confirm whether your cards support MIG before designing around it.',
          'If you time-slice, set a memory cap in the application today.']),
 ],
},
{
 'node': 'serving-llms', 'slug': 'serving-a-model-like-a-production-service',
 'title': 'Serving a model like a production service', 'minutes': 12, 'added': D,
 'dek': 'vLLM behind a Gateway, with readiness that reflects model load rather than process '
        'start &mdash; which is where most first attempts go wrong.',
 'body': [
  ('p', 'A model server is an ordinary HTTP service with three unusual properties: it takes '
        'minutes to become useful, it holds a lot of state in GPU memory, and its requests vary '
        'in cost by two orders of magnitude. Every default in Kubernetes is tuned for services '
        'with none of those properties.'),
  ('h2', 'A minimal vLLM deployment, annotated'),
  ('code', 'apiVersion: apps/v1\n'
           'kind: Deployment\n'
           'metadata: { name: llm }\n'
           'spec:\n'
           '  replicas: 1\n'
           '  template:\n'
           '    spec:\n'
           '      containers:\n'
           '        - name: vllm\n'
           '          image: vllm/vllm-openai:latest\n'
           '          args:\n'
           '            - --model=/models/llama-3.1-8b\n'
           '            - --gpu-memory-utilization=0.90\n'
           '            - --max-model-len=8192\n'
           '          ports: [{ containerPort: 8000 }]\n'
           '          resources:\n'
           '            limits: { nvidia.com/gpu: 1, memory: 32Gi }\n'
           '          volumeMounts:\n'
           '            - { name: models, mountPath: /models, readOnly: true }\n'
           '            - { name: shm, mountPath: /dev/shm }\n'
           '      volumes:\n'
           '        - name: models\n'
           '          persistentVolumeClaim: { claimName: model-weights }\n'
           '        - name: shm                      # NOT optional\n'
           '          emptyDir: { medium: Memory, sizeLimit: 8Gi }'),
  ('gotcha', '<b>That <code>/dev/shm</code> volume is the single most common missing line.</b> '
             'The default shared-memory segment in a container is 64&nbsp;MB. PyTorch uses shared '
             'memory for inter-process communication, so anything with tensor parallelism or '
             'multiple workers crashes with an opaque "bus error" or a NCCL failure that reads '
             'like a GPU problem. It is not &mdash; it is 64&nbsp;MB of /dev/shm.'),
  ('h2', 'Model load time breaks every probe default'),
  ('p', 'Loading 16&nbsp;GB of weights from a network volume into GPU memory takes anywhere from '
        '40 seconds to 6 minutes. With default probes, the container is killed and restarted '
        'before it finishes, forever, and the logs show a half-finished load each time.'),
  ('code', 'startupProbe:\n'
           '  httpGet: { path: /health, port: 8000 }\n'
           '  failureThreshold: 60\n'
           '  periodSeconds: 10          # up to 10 minutes to load\n\n'
           'readinessProbe:\n'
           '  httpGet: { path: /health, port: 8000 }\n'
           '  periodSeconds: 5\n\n'
           'livenessProbe:\n'
           '  httpGet: { path: /health, port: 8000 }\n'
           '  periodSeconds: 30\n'
           '  failureThreshold: 3        # 90s of failure before a restart that costs minutes'),
  ('p', 'Be conservative with liveness specifically. Restarting a model server is not cheap &mdash; '
        'you pay the full load time again &mdash; so a liveness probe that trips on a transient '
        'stall makes an incident worse rather than better.'),
  ('h2', 'Where the weights live'),
  ('ul', ['<strong>Baked into the image</strong> &mdash; simplest, and gives you a 20&nbsp;GB '
          'image to pull on every new node. Fine for one fixed model.',
          '<strong>A ReadOnlyMany volume</strong> &mdash; pulled once, shared by replicas on the '
          'same node. Usually the right default.',
          '<strong>Downloaded by an init container</strong> &mdash; flexible, and every pod '
          'start depends on an external registry being up.',
          '<strong>An OCI artefact</strong> &mdash; weights as a separate layer, cached by the '
          'node like any image. Increasingly the tidiest answer.']),
  ('p', 'Whichever you choose, the first pod on a new node pays the cold cost. That number is the '
        'floor on your scale-up latency, and it is the number to measure before you design '
        'autoscaling.'),
  ('h2', 'Routing: why a plain Service is wrong'),
  ('p', 'A ClusterIP distributes connections roughly evenly and knows nothing about what it is '
        'balancing. For LLM traffic that is actively harmful: requests differ enormously in cost, '
        'and a replica with a warm KV cache for a given prefix is dramatically cheaper to use '
        'than a cold one.'),
  ('code', 'apiVersion: gateway.networking.k8s.io/v1\n'
           'kind: HTTPRoute\n'
           'metadata: { name: llm }\n'
           'spec:\n'
           '  parentRefs: [{ name: ai-gateway }]\n'
           '  rules:\n'
           '    - matches: [{ path: { type: PathPrefix, value: /v1 } }]\n'
           '      timeouts:\n'
           '        request: 300s            # generation is slow; the default will cut it off\n'
           '      backendRefs:\n'
           '        - { name: llm, port: 8000 }'),
  ('p', 'The timeout is the immediate fix &mdash; most ingress defaults are 30 or 60 seconds and '
        'will truncate long generations. Beyond that, the Gateway API Inference Extension adds '
        'model-aware routing: queue depth, KV-cache awareness, and routing by model name to '
        'different backends behind one endpoint. If you are serving more than one model, that is '
        'the thing to look at rather than building it yourself.'),
  ('h2', 'Streaming changes the whole request path'),
  ('p', 'Token streaming is server-sent events over a long-lived connection. Anything in the path '
        'that buffers responses, or closes idle connections, breaks it in a way that looks like a '
        'model problem: the client waits, then gets everything at once, or nothing. Check '
        'buffering and idle timeouts on every proxy between the client and the pod before '
        'debugging the server.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Add the <code>/dev/shm</code> volume now, whether or not you have hit the bug.',
          'Measure your actual cold start from pod creation to first token, and write it down.',
          'Set a <code>startupProbe</code> with a failure threshold based on that measurement.',
          'Raise the request timeout on every proxy in front of the model.']),
 ],
},
{
 'node': 'inference-scale', 'slug': 'scaling-inference-on-real-traffic',
 'title': 'Scaling inference on real traffic', 'minutes': 11, 'added': D,
 'dek': 'Queue-depth autoscaling, cold starts measured in minutes, and the bill as a design '
        'constraint rather than an afterthought.',
 'body': [
  ('p', 'Autoscaling a stateless web service is a solved problem with good defaults. Autoscaling '
        'inference breaks all of those defaults at once, and the reason is simple: a saturated '
        'GPU does not look busy to anything Kubernetes measures by default.'),
  ('h2', 'Why CPU-based HPA fails'),
  ('p', 'A model server at 100% GPU utilisation with a queue thirty requests deep is typically '
        'using 15% CPU. The HPA sees an idle pod and scales <em>down</em>. Meanwhile latency is '
        'climbing and nothing in the control loop knows.'),
  ('ul', ['<strong>GPU utilisation</strong> is better, but it is a poor saturation signal &mdash; '
          'a GPU reads near 100% while still having headroom for more concurrent sequences.',
          '<strong>Queue depth</strong> (<code>num_requests_waiting</code>) is the honest signal. '
          'A non-zero queue means demand exceeds capacity, right now.',
          '<strong>Time to first token</strong> is what users feel, and it is the right thing to '
          'alert on even if you scale on queue depth.']),
  ('code', 'apiVersion: autoscaling/v2\n'
           'kind: HorizontalPodAutoscaler\n'
           'metadata: { name: llm }\n'
           'spec:\n'
           '  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: llm }\n'
           '  minReplicas: 1\n'
           '  maxReplicas: 8\n'
           '  metrics:\n'
           '    - type: Pods\n'
           '      pods:\n'
           '        metric: { name: vllm_num_requests_waiting }\n'
           '        target: { type: AverageValue, averageValue: "4" }\n'
           '  behavior:\n'
           '    scaleUp:\n'
           '      stabilizationWindowSeconds: 0        # react immediately\n'
           '      policies: [{ type: Pods, value: 2, periodSeconds: 60 }]\n'
           '    scaleDown:\n'
           '      stabilizationWindowSeconds: 600      # 10 minutes of calm before shrinking\n'
           '      policies: [{ type: Pods, value: 1, periodSeconds: 300 }]'),
  ('note', 'The asymmetry in <code>behavior</code> is the important part and it is not the '
           'default. Scaling up late costs you a latency spike; scaling down early costs you a '
           'multi-minute cold start on the next request. When those are the two errors available, '
           'you want to be slow to shrink and quick to grow.'),
  ('h2', 'Cold start is the whole design constraint'),
  ('p', 'Add it up honestly: node provisioning 60&ndash;180 seconds, image pull 30&ndash;120, '
        'model load 40&ndash;300, warm-up 10&ndash;30. Three to ten minutes from "we need another '
        'replica" to "it can serve". No autoscaler can hide that.'),
  ('ul', ['<strong>Keep a warm pool.</strong> <code>minReplicas</code> above zero, sized to your '
          'trough, is the only reliable answer for interactive traffic.',
          '<strong>Pre-pull images</strong> with a DaemonSet or a node image that already has '
          'them. Removes the largest variable chunk.',
          '<strong>Over-provision deliberately</strong> with low-priority placeholder pods, so a '
          'node is already warm and a real pod can preempt a placeholder instantly.',
          '<strong>Separate interactive from batch.</strong> Batch work tolerates cold starts and '
          'can use spot capacity; user-facing traffic cannot.']),
  ('h2', 'Scale to zero, honestly'),
  ('p', 'Scale to zero is attractive and only workable when something can hold the first request '
        'while a replica starts, and the caller tolerates minutes. That is true for internal '
        'tools and batch endpoints. It is not true for anything a person is waiting on. Decide '
        'which you have before adopting it.'),
  ('h2', 'The bill as a design constraint'),
  ('p', 'An idle A100 costs roughly the same as a busy one. Utilisation is therefore the only cost '
        'lever that matters, and the arithmetic is unforgiving: a GPU at 20% utilisation is a '
        'GPU you are mostly paying to keep warm.'),
  ('code', '# the number that should be on a dashboard: tokens per GPU-hour\n'
           'sum(rate(vllm_generation_tokens_total[1h]))\n'
           '  / count(DCGM_FI_DEV_GPU_UTIL)\n\n'
           '# and the one that explains it: how much of the time are GPUs doing nothing?\n'
           'avg_over_time(DCGM_FI_DEV_GPU_UTIL[24h])'),
  ('ul', ['<strong>Batch aggressively.</strong> Continuous batching in vLLM is the single largest '
          'throughput win available, and it is a flag.',
          '<strong>Right-size the model.</strong> An 8B model that fits one GPU often beats a 70B '
          'model across four, for tasks where quality is comparable.',
          '<strong>Quantise</strong> when accuracy allows &mdash; fewer GPUs for the same '
          'throughput.',
          '<strong>Spot for batch.</strong> With checkpointing, interruptions are a cost, not a '
          'failure.']),
  ('gotcha', '<b>Watch out for <code>maxSurge</code> on a GPU Deployment.</b> A rolling update '
             'with surge needs a spare GPU for the new pod before the old one goes away. On a '
             'cluster with no idle GPU, the new pod sits <code>Pending</code>, the old one never '
             'terminates, and the rollout hangs until <code>progressDeadlineSeconds</code> '
             'expires. Set <code>maxSurge: 0</code> and accept brief unavailability, or keep a '
             'spare GPU for deploys.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Stop scaling on CPU. Export queue depth and scale on that.',
          'Measure your real cold start, end to end, and set <code>minReplicas</code> from it.',
          'Put tokens per GPU-hour on a dashboard. It changes conversations about cost.',
          'Check <code>maxSurge</code> on every GPU Deployment you own.']),
 ],
},

# ---------------------------------------------------------------- platform
{
 'node': 'capacity', 'slug': 'capacity-bin-packing-and-autoscaling',
 'title': 'Capacity, bin-packing and autoscaling', 'minutes': 10, 'added': D,
 'dek': 'Requests and limits chosen from data, plus node autoscaling that does not thrash.',
 'body': [
  ('p', 'Requests and limits are the two most consequential numbers in a pod spec and the two '
        'most often copied from an example. They do completely different jobs, and confusing them '
        'produces either a cluster that is 80% idle or one that evicts things at random.'),
  ('h2', 'Requests schedule. Limits constrain.'),
  ('ul', ['<strong>Requests</strong> are what the scheduler reserves. They decide where a pod '
          'goes and how full a node is considered. They are not enforced at runtime.',
          '<strong>Limits</strong> are enforced by the kernel. Over a CPU limit, you are '
          'throttled; over a memory limit, you are killed.']),
  ('p', 'So a pod requesting 100m CPU and limited to 2 cores may be scheduled onto a busy node '
        'and then try to use twenty times what it reserved. That works until the node is '
        'contended, at which point everything on it gets slow together.'),
  ('h2', 'QoS classes, and who dies first'),
  ('ul', ['<strong>Guaranteed</strong> &mdash; requests equal limits for every container. Evicted '
          'last.',
          '<strong>Burstable</strong> &mdash; requests set, limits higher or absent. Evicted in '
          'the middle, worst-offender first.',
          '<strong>BestEffort</strong> &mdash; nothing set. Evicted first, always.']),
  ('note', 'This is a decision you make by accident if you do not make it deliberately. A '
           'production database with no resource fields is BestEffort, which means it is the first '
           'thing the kubelet kills under node pressure. Set requests equal to limits on anything '
           'you genuinely cannot lose.'),
  ('h2', 'The CPU-limit argument'),
  ('p', 'There is a real case for setting no CPU limit at all. A CPU limit throttles in fixed '
        'periods, and a latency-sensitive service with a modest limit can be throttled while the '
        'node is mostly idle &mdash; you have taken a latency hit to prevent a problem that was '
        'not occurring. The counter-argument is predictability and noisy neighbours.'),
  ('code', '# the signal that this is happening to you\n'
           'rate(container_cpu_cfs_throttled_seconds_total[5m]) > 0'),
  ('p', 'A defensible position: always set CPU <em>requests</em> accurately, set memory requests '
        'and limits equal, and leave CPU limits off for latency-sensitive services while keeping '
        'them for batch. Memory is different because it is incompressible &mdash; there is no '
        'graceful degradation, only the OOM killer.'),
  ('h2', 'Get the numbers from the cluster, not from a guess'),
  ('code', 'kubectl top pods -n prod --sort-by=memory\n\n'
           '# p95 actual usage over a week, which is what a request should be based on\n'
           'quantile_over_time(0.95,\n'
           '  container_memory_working_set_bytes{namespace="prod"}[7d])\n\n'
           '# requested versus used, per namespace - your idle percentage\n'
           'sum(kube_pod_container_resource_requests{resource="cpu"}) by (namespace)\n'
           '  / sum(rate(container_cpu_usage_seconds_total[1h])) by (namespace)'),
  ('p', 'VPA in recommendation mode is worth running for this even if you never let it act: it '
        'watches real usage and tells you what it would set, which is a better starting point '
        'than anyone’s intuition.'),
  ('h2', 'Node autoscaling, and consolidation'),
  ('p', 'The Cluster Autoscaler adds nodes from predefined groups when pods are unschedulable. '
        'Karpenter instead picks instance types to fit the pending pods, and continuously '
        'consolidates &mdash; replacing several underused nodes with one cheaper node.'),
  ('gotcha', '<b>Consolidation moves running pods, and it will respect only what you have told it '
             'to respect.</b> Without a PodDisruptionBudget, consolidating a node can take down '
             'every replica of a service at once, legitimately, because nothing said otherwise. '
             'Every workload that matters needs a PDB <em>before</em> you enable consolidation.'),
  ('code', 'apiVersion: policy/v1\n'
           'kind: PodDisruptionBudget\n'
           'metadata: { name: api }\n'
           'spec:\n'
           '  minAvailable: 2            # or maxUnavailable: 1\n'
           '  selector:\n'
           '    matchLabels: { app: api }'),
  ('p', 'Also mind the interaction with topology spread: a pod spread across three zones with '
        '<code>whenUnsatisfiable: DoNotSchedule</code> constrains which nodes the autoscaler can '
        'usefully add. Unschedulable pods with an autoscaler that is doing nothing is almost '
        'always a constraint it cannot satisfy, not a broken autoscaler.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Find every pod with no resource fields. Those are BestEffort and will die first.',
          'Set memory requests equal to limits on anything stateful.',
          'Check for CFS throttling on your latency-sensitive services.',
          'Write PDBs before enabling consolidation, not after the first incident.']),
 ],
},
{
 'node': 'slo-observability', 'slug': 'slos-people-actually-use',
 'title': 'SLOs people actually use', 'minutes': 9, 'added': D,
 'dek': 'Three signals per service, one dashboard, and alerts that correspond to someone '
        'being paged.',
 'body': [
  ('p', 'Most Kubernetes monitoring setups collect everything and tell you nothing. The failure '
        'is not technical &mdash; it is that nobody decided what "working" means before building '
        'the dashboards.'),
  ('h2', 'Delete half your alerts first'),
  ('p', 'Before adding anything, go through what fires today and ask one question of each: '
        '<em>when this fired, did a human do something?</em> If the honest answer is no, it is not '
        'an alert. It is a dashboard panel at best.'),
  ('p', 'An alert nobody acts on is worse than no alert, because it trains the team to ignore the '
        'channel where the real one will arrive. The strongest predictor of whether monitoring '
        'works is not coverage, it is how many pages people trust.'),
  ('h2', 'Three signals is enough'),
  ('ul', ['<strong>Availability</strong> &mdash; the fraction of requests that did not fail.',
          '<strong>Latency</strong> &mdash; the fraction served faster than a threshold you chose '
          'deliberately.',
          '<strong>Saturation</strong> &mdash; how close the thing is to a limit, so you have '
          'warning before the first two move.']),
  ('code', '# availability, as a ratio - not a count of errors\n'
           'sum(rate(http_requests_total{status!~"5.."}[5m]))\n'
           '  / sum(rate(http_requests_total[5m]))\n\n'
           '# latency, as a ratio of requests inside the target\n'
           'sum(rate(http_request_duration_seconds_bucket{le="0.5"}[5m]))\n'
           '  / sum(rate(http_request_duration_seconds_count[5m]))'),
  ('note', 'Express latency as <strong>"what fraction was fast enough"</strong> rather than as a '
           'percentile. Histogram-derived percentiles cannot be averaged or aggregated correctly '
           'across instances, and a ratio can. It also matches how you state an objective: 99% of '
           'requests under 500&nbsp;ms.'),
  ('h2', 'Alert on burn rate, not on breach'),
  ('p', 'A 99.9% monthly objective gives you about 43 minutes of error budget. Alerting the moment '
        'you dip below 99.9% in a five-minute window is pure noise. Alerting when you are '
        'consuming the budget fast enough to exhaust it is the signal.'),
  ('code', '# fast burn: 2% of a 30-day budget in an hour -> page\n'
           '- alert: ErrorBudgetBurningFast\n'
           '  expr: |\n'
           '    (1 - (sum(rate(http_requests_total{status!~"5.."}[1h]))\n'
           '          / sum(rate(http_requests_total[1h])))) > 14.4 * 0.001\n'
           '  for: 2m\n'
           '  labels: { severity: page }\n\n'
           '# slow burn: on course to exhaust it this week -> ticket, not a page\n'
           '- alert: ErrorBudgetBurningSlow\n'
           '  expr: |\n'
           '    (1 - (sum(rate(http_requests_total{status!~"5.."}[6h]))\n'
           '          / sum(rate(http_requests_total[6h])))) > 6 * 0.001\n'
           '  for: 30m\n'
           '  labels: { severity: ticket }'),
  ('p', 'Two severities, two response paths. The fast burn wakes someone; the slow burn becomes '
        'work on Monday. That distinction is what makes an on-call rotation survivable.'),
  ('h2', 'Cluster-level alerts worth keeping'),
  ('ul', ['A node <code>NotReady</code> for more than five minutes.',
          'Pods in <code>CrashLoopBackOff</code> for more than fifteen.',
          'PersistentVolume above 85% full &mdash; with hours of warning, not minutes.',
          'Certificates expiring within fourteen days.',
          'A Deployment with fewer ready replicas than its PDB requires.']),
  ('p', 'Notably absent: anything about individual pod restarts, CPU above a threshold, or memory '
        'above a threshold. Those are symptoms, they fire constantly, and they are what dashboards '
        'are for.'),
  ('h2', 'Cardinality is how this gets expensive'),
  ('gotcha', '<b>One label with unbounded values will cost more than the rest of your monitoring '
             'combined.</b> A <code>user_id</code>, a request path with an id in it, or a pod name '
             'on a high-churn Deployment creates a new time series per value, forever. Normalise '
             'paths to route templates before they reach the metric, and keep ids in logs and '
             'traces where they belong.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['List every alert that fired last month and delete the ones nobody acted on.',
          'Pick one service and write down its three signals and one objective.',
          'Replace one threshold alert with a burn-rate alert and compare the noise.',
          'Find your highest-cardinality metric before your bill does.']),
 ],
},
{
 'node': 'extend-k8s', 'slug': 'extending-kubernetes-yourself',
 'title': 'Extending Kubernetes yourself', 'minutes': 12, 'added': D,
 'dek': 'A CRD and controller with controller-runtime &mdash; which is also the shortest '
        'honest route to your first upstream contribution.',
 'body': [
  ('p', 'Writing a controller changes how you read everything else. Once you have implemented a '
        'reconcile loop, the behaviour of every built-in controller becomes predictable, '
        'including the parts that look like bugs.'),
  ('h2', 'Start with the question of whether you should'),
  ('p', 'An operator is justified when there is <em>operational knowledge</em> to encode &mdash; '
        'how to safely upgrade this database, how to fail over, how to resize without data loss. '
        'If all you need is "apply this YAML with some values filled in", that is a Helm chart or '
        'a Kustomize overlay, and a controller is a daemon you now have to keep alive.'),
  ('h2', 'A CRD is a schema plus a status'),
  ('code', '// api/v1alpha1/types.go\ntype CacheSpec struct {\n'
           '    // +kubebuilder:validation:Minimum=1\n'
           '    // +kubebuilder:validation:Maximum=9\n'
           '    Replicas int32 `json:"replicas"`\n\n'
           '    // +kubebuilder:validation:Enum=redis;valkey\n'
           '    Engine string `json:"engine"`\n'
           '}\n\n'
           'type CacheStatus struct {\n'
           '    ReadyReplicas int32              `json:"readyReplicas"`\n'
           '    Conditions    []metav1.Condition `json:"conditions,omitempty"`\n'
           '}\n\n'
           '// +kubebuilder:subresource:status\n'
           '// +kubebuilder:printcolumn:name="Ready",type=integer,JSONPath=`.status.readyReplicas`'),
  ('p', 'Spend the time on validation markers. Every constraint you express in the schema is a '
        'class of bad input the API server rejects before your code runs, which means it is a '
        'branch you never have to write or test. And always use the <code>status</code> '
        'subresource, so updating status cannot conflict with a user editing spec.'),
  ('h2', 'The reconcile contract'),
  ('code', 'func (r *CacheReconciler) Reconcile(ctx context.Context,\n'
           '    req ctrl.Request) (ctrl.Result, error) {\n\n'
           '    var cache v1alpha1.Cache\n'
           '    if err := r.Get(ctx, req.NamespacedName, &cache); err != nil {\n'
           '        // gone: nothing to do. Never requeue a NotFound.\n'
           '        return ctrl.Result{}, client.IgnoreNotFound(err)\n'
           '    }\n\n'
           '    desired := statefulSetFor(&cache)\n'
           '    if err := ctrl.SetControllerReference(&cache, desired, r.Scheme); err != nil {\n'
           '        return ctrl.Result{}, err\n'
           '    }\n\n'
           '    // create-or-update, because this will run many times\n'
           '    if err := r.Patch(ctx, desired, client.Apply,\n'
           '        client.ForceOwnership, client.FieldOwner("cache-operator")); err != nil {\n'
           '        return ctrl.Result{}, err\n'
           '    }\n\n'
           '    cache.Status.ReadyReplicas = readyOf(ctx, r, &cache)\n'
           '    return ctrl.Result{}, r.Status().Update(ctx, &cache)\n'
           '}'),
  ('ul', ['<strong>Idempotent, always.</strong> Reconcile will be called repeatedly for the same '
          'object, with no relationship to how many times it changed.',
          '<strong>Level-triggered, not edge-triggered.</strong> You get "something about this '
          'object may have changed", never a diff. Read the world; do not infer it.',
          '<strong>Return an error to retry.</strong> controller-runtime backs off exponentially. '
          'Do not sleep inside a reconcile.',
          '<strong>Set owner references.</strong> That is what makes deletion clean up after '
          'itself.']),
  ('note', 'Use <strong>server-side apply</strong> with a field owner rather than get-modify-update. '
           'It makes your controller declare only the fields it owns, so it stops fighting with '
           'other controllers, an HPA, or a human editing a different part of the same object. '
           'This is the single biggest improvement available to most hand-written controllers.'),
  ('h2', 'Finalizers, and how to not wedge a namespace'),
  ('gotcha', '<b>A finalizer with a bug makes an object undeletable forever, and a namespace '
             'containing it will hang in <code>Terminating</code> permanently.</b> If your cleanup '
             'cannot succeed &mdash; the external resource is already gone, credentials have '
             'rotated &mdash; you must still remove the finalizer. Treat "cleanup failed '
             'permanently" as a case to log and release, not to retry forever.'),
  ('h2', 'Why this is the contribution route'),
  ('p', 'Having written a controller, you can read any Kubernetes controller, and reading them is '
        'how you find real work to do. The path that actually leads somewhere:'),
  ('ol', ['Build something small with Kubebuilder. A week, and you will understand informers, '
          'work queues and caches properly.',
          'Pick one SIG whose area you now know &mdash; whichever matches the controller you just '
          'wrote.',
          'Start with tests and documentation. Unglamorous, genuinely needed, and the fastest way '
          'to learn a review process without a hard review.',
          'Then fix a real bug, having read the code around it rather than only the issue.']),
  ('p', 'The useful thing about this order is that each step produces something, whether or not '
        'the next one happens. A small operator with users is evidence on its own; so is a merged '
        'documentation fix.'),
  ('h2', 'What to actually do with this'),
  ('ul', ['Scaffold a CRD with Kubebuilder and reconcile it into a ConfigMap. One afternoon.',
          'Convert one get-modify-update to server-side apply and watch the conflicts stop.',
          'Read the ReplicaSet controller in kubernetes/kubernetes. It is shorter than you '
          'expect, and it is the pattern everything else copies.']),
 ],
},
]
