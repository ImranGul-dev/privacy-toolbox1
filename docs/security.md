# Security and Privacy Model

The product avoids claims such as 100% anonymous or absolute anonymity. It validates extension and size, randomizes temporary paths, never logs file contents, avoids storing raw metadata payloads by default, creates short-lived download tokens, and exposes deletion endpoints. Worker isolation and strict CLI timeouts are recommended in production.
