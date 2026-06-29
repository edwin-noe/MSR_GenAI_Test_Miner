# VPS Deployment Guide

This guide helps you deploy **MSR GenAI Test Miner** on a Virtual Private Server (VPS) so that you can run the full mining cycle unattended without tying up your local machine.

---

## Why a VPS?

A full mining run takes **8–24 hours** and makes tens of thousands of GitHub API calls. Running it on a VPS lets you:

- Start the job and disconnect – it keeps running.
- Use a stable, always-on internet connection.
- Keep your laptop free for other work.
- Resume automatically after rate-limit pauses using `run_with_auto_resume.sh`.

---

## Recommended Server Specifications

The miner is **I/O-bound** (mostly waiting for GitHub API responses), so you do not need a powerful CPU or GPU. A modest server is sufficient.

| Resource | Minimum | Recommended |
|---|---|---|
| **CPU** | 1 vCPU | 2 vCPUs |
| **RAM** | 1 GB | 2 GB |
| **Disk** | 10 GB SSD | 20 GB SSD |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| **Network** | 100 Mbps | 1 Gbps |

> **Note:** For datasets larger than 10,000 repositories the tool may consume up to ~1 GB of RAM. Choose 2 GB RAM to be safe.

---

## Budget Estimate

Prices shown are approximate monthly costs as of early 2025. The miner typically finishes within 24 hours, so even the cheapest plan is fine for a one-off run.

| Provider | Plan | vCPU | RAM | Disk | Monthly | Hourly |
|---|---|---|---|---|---|---|
| **DigitalOcean** | Basic Droplet | 1 | 1 GB | 25 GB SSD | ~$6 | ~$0.009 |
| **DigitalOcean** | Basic Droplet | 1 | 2 GB | 50 GB SSD | ~$12 | ~$0.018 |
| **Linode (Akamai)** | Nanode 1 GB | 1 | 1 GB | 25 GB SSD | ~$5 | ~$0.0075 |
| **Linode (Akamai)** | Linode 2 GB | 1 | 2 GB | 50 GB SSD | ~$10 | ~$0.015 |
| **Vultr** | Cloud Compute | 1 | 1 GB | 25 GB SSD | ~$6 | ~$0.009 |
| **Hetzner Cloud** | CX11 | 2 | 2 GB | 20 GB SSD | ~€4 | ~€0.006 |
| **AWS EC2** | t3.micro (free tier) | 2 | 1 GB | — | Free (12 mo) | ~$0.010 |
| **AWS EC2** | t3.small | 2 | 2 GB | — | ~$15 | ~$0.020 |

**💡 Recommendation:** A **$6–$12/month DigitalOcean Droplet** or **€4/month Hetzner CX11** is the best value. If you only run the miner occasionally, you can create the server, run the job, download the output, then destroy the server — total cost **< $1 per run**.

---

## Step-by-Step Deployment

### 1. Create and Connect to Your VPS

```bash
# SSH into your new server (replace with your server's IP)
ssh root@YOUR_SERVER_IP
```

### 2. Install System Dependencies

```bash
# Update packages
apt update && apt upgrade -y

# Install Python, pip, git, and tmux (for background sessions)
apt install -y python3 python3-pip python3-venv git tmux curl

# (Optional) Install Docker for containerized deployment
curl -fsSL https://get.docker.com | sh
```

### 3. Clone the Repository

```bash
git clone https://github.com/edwin-noe/MSR_GenAI_Test_Miner.git
cd MSR_GenAI_Test_Miner
```

### 4. Set Up Your GitHub Token

```bash
# Create a .env file with your GitHub Personal Access Token
# Get a token at: https://github.com/settings/tokens
# Required scopes: public_repo, read:org
echo "GITHUB_TOKEN=your_token_here" > .env
```

### 5. Choose a Deployment Method

---

#### Option A – Docker (Recommended for Simplicity)

```bash
# Build the image
docker build -t msr_genai_test_miner .

# Run in the background; output is saved to ./output on the host
docker run -d \
  --name msr_miner \
  --restart unless-stopped \
  -v "$(pwd)/output:/app/output" \
  -e GITHUB_TOKEN="your_token_here" \
  msr_genai_test_miner

# Follow logs
docker logs -f msr_miner

# Check output files
ls output/
```

---

#### Option B – Python in a tmux Session (Lightweight)

`tmux` keeps the process running after you disconnect from SSH.

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start a tmux session
tmux new-session -s miner

# Inside tmux – start the miner
python -m src.main

# Detach from tmux (the miner keeps running): Ctrl+B then D
# Reconnect later:
tmux attach -t miner
```

---

#### Option C – Auto-Resume Script (Handles Rate Limits Automatically)

The included `run_with_auto_resume.sh` script automatically waits when the GitHub API rate limit is exhausted and then resumes, making it ideal for long unattended runs.

```bash
# Make the script executable
chmod +x run_with_auto_resume.sh

# Set up the virtual environment first
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start in a tmux session
tmux new-session -s miner
./run_with_auto_resume.sh

# Detach: Ctrl+B then D
```

---

#### Option D – systemd Service (Runs as a System Service)

Create a systemd unit so the miner starts automatically on reboot:

```bash
cat > /etc/systemd/system/msr-miner.service << 'EOF'
[Unit]
Description=MSR GenAI Test Miner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/MSR_GenAI_Test_Miner
EnvironmentFile=/root/MSR_GenAI_Test_Miner/.env
ExecStart=/root/MSR_GenAI_Test_Miner/.venv/bin/python -m src.main
Restart=on-failure
RestartSec=30
StandardOutput=append:/root/MSR_GenAI_Test_Miner/output/mining_log.txt
StandardError=append:/root/MSR_GenAI_Test_Miner/output/mining_log.txt

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable msr-miner
systemctl start msr-miner

# Check status
systemctl status msr-miner
journalctl -u msr-miner -f
```

---

### 6. Monitor Progress

```bash
# Tail the mining log
tail -f output/mining_log.txt

# Check the checkpoint file to see how many queries have been processed
cat output/progress.txt

# Check the current output size
wc -l output/validated_repos.csv
```

### 7. Retrieve Results

When the run is complete, copy results to your local machine:

```bash
# From your LOCAL machine:
scp -r root@YOUR_SERVER_IP:~/MSR_GenAI_Test_Miner/output ./output
```

Or use `rsync` for incremental copies during a long run:

```bash
rsync -avz root@YOUR_SERVER_IP:~/MSR_GenAI_Test_Miner/output/ ./output/
```

---

## Resuming After an Interruption

The miner saves a checkpoint after each query batch. If the server restarts or you interrupt the run, simply start it again — it will pick up where it left off:

```bash
# The miner automatically detects output/progress.txt and resumes
python -m src.main
# Output: 🚀 Starting mining from query 456/3456
```

---

## Cost Optimization Tips

1. **Destroy the server after the run** — if you use a provider that charges hourly, a 24-hour run costs only ~$0.25 on the cheapest tier.
2. **Use Hetzner Cloud** — offers some of the best price-to-performance ratios in Europe.
3. **Use AWS Free Tier** — a `t3.micro` instance is free for 12 months if you are a new AWS customer.
4. **Reserved / Spot instances** — for repeated runs, AWS Reserved or Spot instances can reduce cost by 50–90%.
5. **Use `--no-enrich` mode** — reduces run time to 2–4 hours and API calls by ~80%, which may fit within the GitHub free tier rate limits in a single session.

---

## Security Checklist

- [ ] Store your GitHub token in the `.env` file only — **never hard-code it** in source files.
- [ ] Use SSH key authentication instead of a password for your VPS.
- [ ] Restrict SSH access to your IP in the VPS firewall settings.
- [ ] Add `.env` to `.gitignore` (it already is) to prevent accidental commits.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Permission denied` on `run_with_auto_resume.sh` | Run `chmod +x run_with_auto_resume.sh` |
| Mining stops after ~1 hour | GitHub rate limit hit; use `run_with_auto_resume.sh` or wait and re-run |
| `ModuleNotFoundError` | Activate the virtual environment: `source .venv/bin/activate` |
| Output directory missing | Run `mkdir -p output` before starting |
| SSH connection drops mid-run | Use `tmux` or `screen` so the process continues after disconnect |
| Docker container exits immediately | Check logs with `docker logs msr_miner` and verify `.env` token |
