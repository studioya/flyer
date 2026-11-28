import json, subprocess, sys, os
shots = json.load(open('shots.json')); scale = float(sys.argv[1]); names = sys.argv[2:] or list(shots)
base = os.environ.get('BASE', '')
jobs = [[f'out/{n}.png', f"{base}&{shots[n]['q']}&w={int(shots[n]['w']*scale)}&h={int(shots[n]['h']*scale)}"] for n in names]
env = dict(os.environ, NODE_PATH=subprocess.check_output(['npm', 'root', '-g'], text=True).strip())
subprocess.run(['node', 'shoot.js', json.dumps(jobs)], env=env, check=True)
