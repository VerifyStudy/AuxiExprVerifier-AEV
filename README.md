# AuxiExprVerifier-AEV
辅助表达式验证工具
# Run
## Run a sibgle file
./main
## Run by a folder
./scripts/run.py -i your-folder -o your-output-folder
# .vsocde/launch.json
My vscode configure file
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [{
            "name": "Python: ScriptsRun",
            "type": "python",
            "request": "launch",
            "program": "${workspaceRoot}/scripts/run.py",
            "console": "integratedTerminal",
            "args": [
                "-i", "loop-invariants/",
                "-o", "loop-invariants-auxi/"
            ]
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
        }
    ]
}
```
