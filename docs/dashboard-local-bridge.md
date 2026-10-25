# NOVA Command Center — Local Bridge

The public dashboard is static. This read-only bridge lets it display selected live data from the Windows workspace when the dashboard is opened on the **same PC** as the bridge.

## Security model

- Binds only to `127.0.0.1:8765`; never change the bind address to `0.0.0.0`.
- Requires a random bearer token.
- Accepts browser requests only from `https://nova-workplace.netlify.app`.
- Exposes OS/Python metadata and aggregate finance totals only.
- Has no MCP, file-read, command-execution, memory, or finance-write endpoint.
- The dashboard token is entered manually and held in page memory only. It is not written to localStorage.
- The bridge does **not** claim the NOVA agent itself is online; bridge connectivity and runtime process status are different.

## Start on Windows

1. Open PowerShell.
2. Download the bridge into your actual workspace root (alongside the `finance` folder):

```powershell
Set-Location "E:\ai workspace"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/kelvinkbk/nova-workspace/main/dashboard_bridge.py" -OutFile ".\dashboard_bridge.py"
```

3. Create a temporary random token and start the server:

```powershell
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] 32
$rng.GetBytes($bytes)
$rng.Dispose()
$env:NOVA_DASHBOARD_TOKEN = [Convert]::ToBase64String($bytes)
Write-Host "Paste this private token into the dashboard:"
Write-Host $env:NOVA_DASHBOARD_TOKEN
python .\dashboard_bridge.py
```

Keep this terminal open. The token changes when you restart the bridge. Do not share it or commit it.

4. Open [NOVA Command Center](https://nova-workplace.netlify.app), paste the token into **Local NOVA connection**, and click **Connect**.
5. The dashboard refreshes live status every 15 seconds. Click **Disconnect** to clear the token from the page.

## Troubleshooting

- **Unauthorized:** reconnect using the token printed by the currently running bridge.
- **Connection refused:** start the bridge and keep its terminal open.
- **Origin not allowed:** use the exact Netlify site URL above.
- **Ledger unavailable:** the bridge cannot find/read `finance/ledger.sqlite3`. It deliberately does not create a database or show missing data as zero.
- **Browser blocks localhost access:** do not disable browser security. Share the exact console error so we can choose a secure alternative.
- Stop the bridge with `Ctrl+C`.

## Limitations

This first version provides live bridge connectivity, host/Python metadata, bridge uptime, and aggregate evidence-backed finance totals if the local ledger exists. It does not expose the MCP server, execute commands, list files, read conversation memory, or independently confirm that the NOVA runtime process is running.
