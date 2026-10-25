# NOVA Command Center — Local Bridge

The public dashboard is static. To display live local data, a read-only bridge can run on the same Windows PC as the NOVA workspace.

## Security requirements
- Bind only to 127.0.0.1, never 0.0.0.0.
- Require a random bearer token.
- Allow only the exact Netlify dashboard origin.
- Expose aggregate system and finance status only; never expose MCP, file reads, command execution, or finance writes.
- Never commit tokens, environment files, local databases, or payment configuration.

## Important limitation
A bridge running on the laptop can only be reached from a browser on that same laptop. The bridge should not claim that the NOVA agent itself is online unless the runtime process is independently checked. If browser security blocks localhost access from the HTTPS site, do not disable browser security; use a reviewed alternative.
