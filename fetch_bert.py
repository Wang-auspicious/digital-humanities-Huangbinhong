import subprocess, shutil, os
remote = "mirukj@10.50.40.187"
remote_dir = "/media/mirukj/6e204f04-b878-4d6e-8c5a-ad25aa98eff4/颈动脉斑块/bert_project"
local_dir = r"D:\Desktop\VAST CHALLENGE"
for fname in ["bertopic_report.txt", "bertopic_results.json"]:
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", remote, f"cat '{remote_dir}/{fname}'"],
        capture_output=True
    )
    with open(os.path.join(local_dir, fname), "wb") as f:
        f.write(r.stdout)
    print(f"{fname}: {len(r.stdout)} bytes")
