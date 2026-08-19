# Adjudicated behavior corpus

Command → verdict rulings accumulated by the prototype guard across three
projects. Each entry is a decision an operator stood behind: what a guard
given the described policy must answer for exactly this command line.
`silent` means "no opinion — hand the call to the permission rules".

These are **rulings, not design**: they say nothing about how an engine or
its configuration API should be shaped. Where a ruling conflicts with the
specification, the specification wins and the conflict must be reported.

## How to read the policy contexts

Verdicts only mean something against a policy. Three policy contexts apply
below. Three facts hold across all of them:

**The shell-wrapper layer in effect** (declared value-taking options, and
positional operands a wrapper keeps for itself before the wrapped command
begins — several rulings depend on these exact declarations, including one
deliberately fictional flag): `sudo` (values: `-u --user -g --group -p
--prompt`; note `--prompt-file` is *not* declared — a ruling depends on
that), `doas` (`-u -C`), `env` (`-u --unset -C --chdir -S
--split-string`), `command`, `builtin`, `exec` (`-a`), `nohup`, `setsid`,
`time` (`-f --format -o --output`), `nice` (`-n --adjustment`), `ionice`
(`-c -n -p`), `stdbuf` (`-i -o -e --input --output --error`), `timeout`
(values `-s --signal -k --kill-after`; keeps **one** positional operand,
the duration), `chrt` (`-p`; one operand), `taskset` (`-c -p`; one
operand), `flock` (`-w --wait -E --conflict-exit-code`; one operand),
`xargs` (`-n -P -I -d -E -L -s --max-args --max-procs --replace
--delimiter --max-lines`). Undeclared wrapper options are presumed bare.

**Empty operands never satisfy a bare operand matcher**: a grant stated as
"every operand matches …" requires at least one operand — `stubtool clean`
with no operands is *not* vacuously granted, it asks.

**Each section's registry**: section A runs against git + docker (plus the
wrapper layer); section B against the three stub fixtures (plus the
wrapper layer; no git/docker registered — immaterial to every B verdict);
section C against section A's tools plus the four infra tools.

### Context A — real-tool starter policy (git, docker)

- **git** — deny: forced/mirror/delete pushes, `filter-branch`,
  `filter-repo`, reflog expiry/deletion, `update-ref -d`, `gc --prune`.
  Ask: any push; `commit --amend`; rebase; `reset --hard/--merge/--keep`;
  clean; restore; checkout with `--` (pathspec), `-f` or `--force`;
  switch with `--discard-changes`, `-f` or `--force`; `stash
  drop/clear`; branch deletion only (`-d`, `-D`, `--delete`); tag
  deletion or forced movement (`-d`, `--delete`, `-f`, `--force`);
  `worktree remove/prune`.
  Allow (hedged, §6.3 of the specification): `commit` with `-m/--message`.
  Global options (`-C`, `--git-dir`, `-c`, `--exec-path`, …) are declared,
  so rules still fire behind them; no global is accounted for by the allow.
- **docker** (aliases podman, nerdctl) — ask: push in all spellings
  (`push`, `image push`, `manifest push`, `compose push`,
  `buildx imagetools create`); publish-capable build flags on `build`
  and `buildx build` (`--push`, `--output`/`-o`) and on `buildx bake`
  (`--push` only); all prunes; `login`/`logout`.
  Handoffs: `run IMAGE [cmd]`, `exec CONTAINER cmd`, and both
  `compose` forms — one kept operand, then the inner command begins;
  the image/service/container name is never read as a program. The
  handoffs' value-taking options (exactly — locating the kept operand
  depends on them): run/compose-run consume a value for `-v --volume -e
  --env -p --publish -w --workdir -u --user -l --label -h --hostname -m
  --memory -a --attach --name --entrypoint --network --mount --env-file
  --label-file --add-host --device --dns --expose --platform --pull
  --restart --runtime --security-opt --shm-size --stop-signal --sysctl
  --tmpfs --ulimit --userns --volumes-from --volume-driver --cap-add
  --cap-drop --gpus --cgroupns --cidfile --group-add --ip --isolation
  --link --log-driver --log-opt --mac-address --memory-swap --pid
  --pids-limit --storage-opt --uts --cpus --health-cmd`; exec/compose-exec
  for `-e --env -u --user -w --workdir --env-file --detach-keys`; every
  other option (`--rm`, `-d`, `-it`, …) is bare.

### Context B — engine-behavior policy (hypothetical tools)

Cases below that use `stubtool`/`stub2`, `stubcli` or `stubalways` are
engine-behavior rulings against deliberately artificial tools:

- **stubtool** (alias `stub2`) — a *gated* tool: dangerous unless a grant
  holds, default verdict ask. Accounted (closed-world) flags:
  `--syntax-check --list-tasks -i --inventory --tags --limit --mode`;
  value-taking: `-i --inventory --tags --limit --mode`. Accounted
  environment assignments: `STUB_QUIET`, `STUB_TARGET`. Grants: (1) at
  least one of `--syntax-check`/`--list-tasks` operative; (2) every
  operand matches the anchored regex `^(?:.*/)?validates?\.ya?ml$`
  (anchored and dot-escaped — an unanchored reading would wrongly pass
  `validates.yaml.bak`); (3) subcommand `clean` with
  every operand a path under `/tmp` or `.scratch` (resolved before
  comparison); (4) subcommand `apply` with `--mode` valued `dry-run` or
  `check`; (5) subcommand `apply` with `STUB_TARGET` a path under `/tmp`,
  glob `/home/*/scratch` (no `/` crossing), or regex `^/mnt/\w+/build$`
  (resolved before comparison). Rules: subcommand `wipe` carries both an
  ask and a deny (ranking, not order, must decide); subcommand `touch`
  asks even where a grant holds; assignment `STUB_DANGER` denies.
  Handoffs: `exec` (own value-opt `-u`, one kept operand), `run` (one
  kept operand).
- **stubcli** — gated with default verdict **deny**; grant: at least one
  operand matches the anchored read-verb regex `^(list|show|catalog)$`;
  deny rule: any operand matches the anchored write-verb regex
  `^(create|delete|set)$`.
- **stubalways** — no rules, no grants, default verdict deny: every use
  is the operator's.

### Context C — infra project policy (ansible, openstack/osmp, hcloud)

- **ansible-playbook** — gated, default verdict **deny**. Grants: (1) at
  least one of `--syntax-check --list-tasks --list-tags --list-hosts
  --help --version` operative; (2) every operand a path under
  `playbooks/check` (resolved before comparison). Closed-world
  (accounted) flags, exactly: `-i --inventory -e --extra-vars -l
  --limit -t --tags --skip-tags -v -vv -vvv -vvvv --verbose --diff
  --check -u --user -c --connection -f --forks --private-key
  --key-file --vault-password-file --vault-id --start-at-task --step
  --flush-cache --force-handlers --list-hosts --module-path -M
  --ssh-common-args --ssh-extra-args --become -b --become-user
  --become-method --timeout -T` plus the six local-question flags of
  grant (1). Value-taking (arity), exactly: `-i --inventory -e
  --extra-vars -l --limit -t --tags --skip-tags -u --user -c
  --connection -f --forks --private-key --key-file
  --vault-password-file --vault-id --start-at-task --module-path -M
  --ssh-common-args --ssh-extra-args --become-user --become-method
  --timeout -T` — note `-e` and `-i` are both accounted *and*
  value-taking; two silent rulings depend on that. Unknown flags leave
  a run unproven.
- **ansible** (ad-hoc) — gated, default deny; only the local-question
  flags above are granted. Its closed world is ansible-playbook's
  accounted set plus `-m --module-name -a --args`; its value-taking set,
  exactly: `-m --module-name -a --args -i --inventory -l --limit -u
  --user -e --extra-vars`.
- **openstack** (alias `osmp`) — gated, default deny; grants: any operand
  matching the anchored read-verb regex `^(list|show|catalog|help)$`,
  or `--help`/`--version`; deny rule: any operand matching the anchored
  write-verb regex
  `^(create|delete|remove|set|unset|add|update|restart|reboot|start|stop|pause|unpause|suspend|resume|resize|rebuild|migrate|shelve|unshelve|lock|unlock|rescue|unrescue|evacuate|attach|detach|associate|disassociate|upload|import|export|purge|prune)$`.
  Accounted (closed-world) flags, exactly: `--help --version -f --format
  -c --column --os-cloud --os-project-name --os-region-name --long
  --max-width --noindent --quiet --debug --sort-by --all --json -o
  --output -n --name`; **no flag is declared value-taking** (a ruling
  depends on `--help` being accounted as well as granted).
- **hcloud** — same shape, same accounted-flag set, likewise no
  value-taking flags; read verbs `^(list|describe)$`; write-verb
  deny regex
  `^(create|delete|remove|update|add|attach|detach|enable|disable|rebuild|reset|poweron|poweroff|reboot|shutdown)$`.

## The rulings

### Engine behavior (context B) — 174 rulings

- `stubtool --syntax-check site.yml` → **silent**
- `stubtool site.yml --syntax-check` → **silent**
- `stubtool -i prod --syntax-check site.yml` → **silent**
- `stubtool --tags foo --syntax-check deploy.yml` → **silent**
- `stubtool --list-tasks deploy.yml` → **silent**
- `stubtool run/validates.yaml` → **silent**
- `stubtool deploy.yml` → **ask**
- `stubtool -i prod deploy.yml` → **ask**
- `stubtool validates.yaml -e target=prod` → **ask**
- `stubtool deploy.yml -i --syntax-check` → **ask**
- `stubtool deploy.yml --tags --syntax-check` → **ask**
- `stubtool deploy.yml --limit` → **ask**
- `stubtool deploy.yml -e msg='--syntax-check'` → **ask**
- `stubtool --syntax-check deploy.yml --unknown` → **ask**
- `stubtool wipe --syntax-check` → **deny**
- `stubtool touch --syntax-check` → **ask**
- `stubtool other --syntax-check` → **silent**
- `STUB_QUIET=1 stubtool --syntax-check site.yml` → **silent**
- `STUB_UNKNOWN=1 stubtool --syntax-check site.yml` → **ask**
- `STUB_DANGER=1 stubtool --syntax-check site.yml` → **deny**
- `STUB_QUIET=1 stubtool deploy.yml` → **ask**
- `STUB_TARGET=/tmp/x stubtool apply` → **silent**
- `STUB_TARGET=/prod stubtool apply` → **ask**
- `stubtool apply` → **ask**
- `STUB_TARGET=/tmp/../etc stubtool apply` → **ask**
- `STUB_TARGET=/tmp/../../root stubtool apply` → **ask**
- `STUB_TARGET=/tmp/a/../b stubtool apply` → **silent**
- `STUB_TARGET=/tmp stubtool apply` → **silent**
- `STUB_TARGET=/tmpevil stubtool apply` → **ask**
- `STUB_TARGET=tmp/x stubtool apply` → **ask**
- `STUB_TARGET=~/tmp stubtool apply` → **ask**
- `STUB_TARGET=/home/yann/scratch stubtool apply` → **silent**
- `STUB_TARGET=/home/yann/scratch/build stubtool apply` → **silent**
- `STUB_TARGET=/home/a/b/scratch stubtool apply` → **ask**
- `STUB_TARGET=/home/yann/other stubtool apply` → **ask**
- `STUB_TARGET=/mnt/data/build stubtool apply` → **silent**
- `STUB_TARGET=/mnt/data/builds stubtool apply` → **ask**
- `STUB_TARGET=/mnt/data/build/sub stubtool apply` → **ask**
- `STUB_TARGET=/home/yann/scratch/../../etc stubtool apply` → **ask**
- `STUB_TARGET=/mnt/data/build/../../../etc stubtool apply` → **ask**
- `stubtool apply --mode dry-run` → **silent**
- `stubtool apply --mode check` → **silent**
- `stubtool apply --mode destroy` → **ask**
- `stubtool apply --mode` → **ask**
- `stubtool --syntax-check STUB_DANGER=1` → **silent**
- `STUB_QUIET=1 STUB_TARGET=/tmp/x stubtool apply` → **silent**
- `STUB_DANGER+=1 stubtool --syntax-check site.yml` → **deny**
- `STUB_QUIET+=1 stubtool --syntax-check site.yml` → **silent**
- `stub_danger=1 stubtool --syntax-check site.yml` → **ask**
- `sudo stubtool deploy.yml` → **ask**
- `sudo stubtool wipe` → **deny**
- `env stubtool wipe` → **deny**
- `time stubtool wipe` → **deny**
- `nohup stubtool wipe` → **deny**
- `xargs stubtool wipe` → **deny**
- `eval stubtool wipe` → **deny**
- `eval "stubtool wipe"` → **deny**
- `eval 'stubtool wipe'` → **deny**
- `eval "stubtool --syntax-check a.yml"` → **silent**
- `eval "make check"` → **silent**
- `eval "sh -c 'stubtool wipe'"` → **deny**
- `eval` → **silent**
- `sudo stubtool --syntax-check site.yml` → **silent**
- `sudo -u deployer stubtool wipe` → **deny**
- `sudo --user=deployer stubtool wipe` → **deny**
- `nice -n 5 stubtool wipe` → **deny**
- `timeout 30 stubtool wipe` → **deny**
- `timeout -k 5 30 stubtool wipe` → **deny**
- `xargs -n 1 stubtool wipe` → **deny**
- `sudo --unknown-flag stubtool wipe` → **deny**
- `sudo env STUB_DANGER=1 stubtool --syntax-check a.yml` → **deny**
- `sudo nice -n 5 stubtool wipe` → **deny**
- `env STUB_QUIET=1 stubtool --syntax-check a.yml` → **silent**
- `sudo -u stubtool wipe` → **silent**
- `sudo --prompt-file /tmp/p stubtool wipe` → **ask**
- `sudo sh -lc 'stubtool wipe'` → **deny**
- `sudo apt install ripgrep` → **silent**
- `time make check` → **silent**
- `sh -c 'stubtool wipe'` → **deny**
- `bash -c 'stubtool deploy.yml'` → **ask**
- `sh -c 'stubtool --syntax-check a.yml'` → **silent**
- `bash -lc 'stubtool wipe'` → **deny**
- `sh -c 'sh -c "stubtool wipe"'` → **deny**
- `sh -c 'make check'` → **silent**
- `python3 -c 'print(1)'` → **silent**
- `myrunner stubtool wipe` → **silent**
- `stubcli server list` → **silent**
- `stubcli security group rule list` → **silent**
- `stubcli catalog list` → **silent**
- `stubcli server delete x` → **deny**
- `stubcli server frobnicate x` → **deny**
- `stubcli` → **deny**
- `stubcli server list && stubcli server delete x` → **deny**
- `stubcli server delete list` → **deny**
- `stubalways anything at all` → **deny**
- `stubalways` → **deny**
- `sudo stubalways --help` → **deny**
- `grep stubtool README.md` → **silent**
- `ls ../stubtool` → **silent**
- `cat docs/env` → **silent**
- `stubtool exec box stubtool wipe` → **deny**
- `stubtool exec -u root box stubtool wipe` → **deny**
- `stubtool exec box stubtool --syntax-check a.yml` → **ask**
- `stubtool exec box echo hi` → **ask**
- `stubtool build .` → **ask**
- `stubtool run image stubtool wipe` → **deny**
- `stubtool run stubtool wipe` → **ask**
- `stubtool run image --syntax-check a.yml` → **ask**
- `stubtool clean /tmp/x` → **silent**
- `stubtool clean /tmp/x /tmp/y` → **silent**
- `stubtool clean .scratch/build` → **silent**
- `stubtool clean ./.scratch/build` → **silent**
- `stubtool clean /tmp/x /etc/passwd` → **ask**
- `stubtool clean /etc/passwd` → **ask**
- `stubtool clean /tmp/../etc` → **ask**
- `stubtool clean .scratch/../secrets` → **ask**
- `stubtool clean .scratch/a/../b` → **silent**
- `stubtool clean` → **ask**
- `stub2 wipe` → **deny**
- `stub2 --syntax-check site.yml` → **silent**
- `stub2 deploy.yml` → **ask**
- `stub2 exec box stubtool wipe` → **deny**
- `stub2 run image stubtool wipe` → **deny**
- `sudo stub2 wipe` → **deny**
- `stub2x wipe` → **silent**
- `echo 'stubtool deploy.yml'` → **silent**
- `stubtool --syntax-check 'my file.yml'` → **ask**
- `stubtool-extra deploy.yml` → **silent**
- `mystubtool deploy.yml` → **silent**
- `cd /srv && stubtool run/validates.yaml` → **silent**
- `stubtool deploy.yml && stubtool --syntax-check a.yml` → **ask**
- `stubtool --syntax-check a.yml && stubtool deploy.yml` → **ask**
- `stubtool --syntax-check a.yml && stubtool b.yml --syntax-check` → **silent**
- `stubtool --syntax-check a.yml; stubtool deploy.yml` → **ask**
- `stubtool --syntax-check a.yml | stubtool deploy.yml` → **ask**
- `stubtool --syntax-check a.yml && stubtool wipe` → **deny**
- `stubtool wipe && stubtool --syntax-check a.yml` → **deny**
- multiline command:

```
stubtool --syntax-check a.yml
stubtool deploy.yml
```

  → **ask**
- multiline command:

```
stubtool deploy.yml
stubtool --syntax-check a.yml
```

  → **ask**
- multiline command:

```
echo hi
stubtool deploy.yml
```

  → **ask**
- multiline command:

```
stubtool --syntax-check a.yml


stubtool deploy.yml
```

  → **ask**
- multiline command:

```
stubtool --syntax-check a.yml
stubtool --list-tasks b.yml
```

  → **silent**
- multiline command:

```
echo "one
stubtool deploy.yml"
```

  → **silent**
- multiline command:

```
stubtool deploy.yml \
--syntax-check
```

  → **silent**
- multiline command:

```
stubtool deploy.yml \
         --syntax-check
```

  → **silent**
- multiline command:

```
stubtool \
--syntax-check site.yml
```

  → **silent**
- `stubtool deploy.yml  # --syntax-check next time` → **ask**
- multiline command:

```
cat > play.yml <<'EOF'
stubtool deploy.yml
EOF
```

  → **silent**
- multiline command:

```
bash <<'EOF'
stubtool deploy.yml
EOF
```

  → **ask**
- multiline command:

```
sh <<SH
stubtool deploy.yml
SH
```

  → **ask**
- `stubtool 'unbalanced` → **ask**
- `echo 'unbalanced` → **silent**
- `make check` → **silent**
- `ls -la && rg TODO src/` → **silent**
- `python3 scripts/build.py --force` → **silent**
- `echo $(stubtool wipe)` → **deny**
- `echo $(stubtool --syntax-check a.yml)` → **silent**
- `VAR=$(stubtool wipe)` → **deny**
- `cat <(stubtool wipe)` → **deny**
- `(stubtool wipe)` → **deny**
- `(cd /srv && stubtool wipe)` → **deny**
- `echo $(date)` → **silent**
- `stubtool --syntax-check $(git rev-parse HEAD).yml` → **silent**
- `echo "$(stubtool wipe)"` → **deny**
- `` echo `stubtool wipe` `` → **deny**
- `stubtool --syntax-check "$(stubtool wipe)"` → **deny**
- `echo '$(stubtool wipe)'` → **silent**
- `` echo '`stubtool wipe`' `` → **silent**
- multiline command:

```
bash <<'SH'
stubtool wipe
SH
```

  → **deny**
- multiline command:

```
python3 - <<'PY'
note = "see `stubtool wipe` for why"
PY
```

  → **silent**
- multiline command:

```
python3 - <<'PY'
s = s.replace("stubtool wipe", "x")
PY
```

  → **silent**
- `echo "$(stubtool --syntax-check a.yml)"` → **silent**
- `echo "$(echo $(stubtool wipe))"` → **deny**
- `echo "no substitution here"` → **silent**

### git and docker starter policy (context A) — 109 rulings

- `git status` → **silent**
- `git log --oneline -20` → **silent**
- `git diff HEAD~1` → **silent**
- `git worktree list` → **silent**
- `git stash list` → **silent**
- `git branch --list` → **silent**
- `git checkout main` → **silent**
- `git tag -a v1 -m release` → **silent**
- `git restore --staged file.py` → **ask**
- `git push` → **ask**
- `git push origin main` → **ask**
- `git -C /srv/repo push` → **ask**
- `git --git-dir=.git commit --amend` → **ask**
- `git commit --amend --no-edit` → **ask**
- `git commit -m x --amend` → **ask**
- *(The three allow rulings below are conditional: if the specification's
  open fact (c) verification retires the allow verdict, they are
  superseded — satisfied by silence — and do not block the parity
  declaration, per §13.)*
- `git commit -m "$(cat msg.txt)"` → **allow**
- `git commit -m "fix $(git rev-parse --short HEAD)"` → **allow**
- `git commit --message "$(cat m)"` → **allow**
- `git commit -m wip` → **silent**
- `git commit -m 'a plain message'` → **silent**
- `git commit -m "$(git push --force)"` → **deny**
- `git commit --amend -m "$(cat m)"` → **ask**
- `git commit -m "$(cat m)" && git push` → **ask**
- `git commit -m "$(cat m)" && git push --force` → **deny**
- `git -C /elsewhere commit -m "$(cat m)"` → **silent**
- `git --exec-path=/tmp/x commit -m "$(cat m)"` → **silent**
- `git commit -F msg.txt` → **silent**
- `git rebase -i main` → **ask**
- `git reset --hard HEAD~1` → **ask**
- `git clean -fd` → **ask**
- `git restore .` → **ask**
- `git checkout -- file.py` → **ask**
- `git switch --discard-changes main` → **ask**
- `git checkout -f main` → **ask**
- `git checkout --force main` → **ask**
- `git checkout -f -- .` → **ask**
- `git switch -f main` → **ask**
- `git switch --force main` → **ask**
- `git checkout main` → **silent**
- `git switch main` → **silent**
- `git stash drop` → **ask**
- `git stash clear` → **ask**
- `git branch -D topic` → **ask**
- `git worktree remove wt` → **ask**
- `git worktree prune` → **ask**
- `git tag -d v1` → **ask**
- `git tag -a -f v1` → **ask**
- `git push --force` → **deny**
- `git push origin --force main` → **deny**
- `git push -f origin main` → **deny**
- `git -C . push --force-with-lease` → **deny**
- `git filter-branch --tree-filter true HEAD` → **deny**
- `git filter-repo --path src` → **deny**
- `docker run --rm alpine git push --force` → **deny**
- `docker run --rm git push --force` → **silent**
- `docker run --rm alpine/git push --force` → **silent**
- `docker run --rm alpine/git:2.45 push --force` → **silent**
- `docker run --rm -v /r:/r alpine git push --force` → **deny**
- `docker exec -u root api git push --force` → **deny**
- `docker compose run git push --force` → **silent**
- `docker exec git push` → **silent**
- `docker compose exec git push` → **silent**
- `docker compose run --rm web git push --force` → **deny**
- `docker compose exec web git push --force` → **deny**
- `podman run --rm alpine git push --force` → **deny**
- `nerdctl run --rm alpine git push --force` → **deny**
- `docker run --rm alpine git status` → **silent**
- `docker run --rm alpine echo hello` → **silent**
- `docker run --rm alpine/curl -sL https://example.com` → **silent**
- `docker run --rm alpine/curl https://example.com` → **silent**
- `docker run --rm myimage --verbose --output /tmp/x` → **silent**
- `docker run --rm postgres:16 postgres --version` → **silent**
- `docker run --rm alpine` → **silent**
- `docker run --rm -d --name web nginx` → **silent**
- `docker run --rm alpine/curl -o git https://example.com` → **ask**
- `docker build .` → **silent**
- `docker compose up -d` → **silent**
- `git reflog expire --expire=now --all` → **deny**
- `git reflog delete HEAD@{2}` → **deny**
- `git update-ref -d refs/heads/topic` → **deny**
- `git gc --prune=now` → **deny**
- `docker push registry.example/app:1` → **ask**
- `docker image push registry.example/app:latest` → **ask**
- `docker manifest push registry.example/app:latest` → **ask**
- `docker compose push` → **ask**
- `docker buildx imagetools create -t registry.example/a:1 registry.example/a:2` → **ask**
- `docker build --push -t app:dev .` → **ask**
- `docker build -t app:dev . --push` → **ask**
- `docker build -o type=registry,name=registry.example/a:dev .` → **ask**
- `docker buildx build --push .` → **ask**
- `docker buildx bake --push` → **ask**
- `docker system prune -a` → **ask**
- `docker image prune -a` → **ask**
- `docker volume prune` → **ask**
- `docker network prune` → **ask**
- `docker container prune` → **ask**
- `docker builder prune` → **ask**
- `docker buildx prune` → **ask**
- `docker login registry.example` → **ask**
- `docker logout registry.example` → **ask**
- `docker build -t app:dev .` → **silent**
- `docker run --rm -it app:dev` → **silent**
- `docker rm -f app-test` → **silent**
- `docker rmi app:dev` → **silent**
- `docker volume rm app-data` → **silent**
- `docker image ls` → **silent**
- `docker system df` → **silent**
- `docker pull debian:trixie-slim` → **silent**
- `docker manifest inspect registry.example/app:latest` → **silent**

### Infra project additions (context C) — 33 rulings

- `.venv/bin/ansible-playbook playbooks/check/validate.yml` → **silent**
- `.venv/bin/ansible-playbook playbooks/check/render.yml -e render_root=/tmp/out` → **silent**
- `ansible-playbook ./playbooks/check/validate.yml -i tests/fixtures/valid-full` → **silent**
- `ansible-playbook playbooks/preflight.yml --syntax-check` → **silent**
- `ansible-playbook --syntax-check playbooks/nodes.yml` → **silent**
- `ansible-playbook playbooks/nodes.yml --list-tasks` → **silent**
- `ansible-playbook --version` → **silent**
- `ansible-playbook playbooks/preflight.yml` → **deny**
- `ansible-playbook playbooks/nodes.yml -e nodes_remove=test1` → **deny**
- `CONFIRM_REAL=1 ansible-playbook playbooks/preflight.yml` → **deny**
- `sudo ansible-playbook playbooks/nodes.yml` → **deny**
- `ansible-playbook playbooks/check/../nodes.yml` → **deny**
- `ansible-playbook playbooks/check/validate.yml playbooks/nodes.yml` → **deny**
- `ansible-playbook playbooks/nodes.yml && rm -rf /tmp/x` → **deny**
- `ansible all -m shell -a whoami` → **deny**
- `ansible --version` → **silent**
- `osmp server list` → **silent**
- `osmp network show default` → **silent**
- `osmp catalog list` → **silent**
- `openstack security group rule list` → **silent**
- `osmp --help` → **silent**
- `osmp server delete fx-probe` → **deny**
- `osmp subnet set --gateway 10.10.0.1 default` → **deny**
- `osmp server frobnicate fx-probe` → **deny**
- `osmp server list && osmp server delete fx-probe` → **deny**
- `osmp server delete list` → **deny**
- `CONFIRM_REAL=1 osmp server delete fx-probe` → **deny**
- `hcloud server list` → **silent**
- `hcloud server describe main` → **silent**
- `hcloud server delete main` → **deny**
- `echo playbooks/preflight.yml` → **silent**
- `just check` → **silent**
- `just test` → **silent**
