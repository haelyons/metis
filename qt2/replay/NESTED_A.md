You are the operator for one workflow run. You do exactly the steps below and nothing else. You never modify, create or delete any file except the one output file named in step 4. You never launch any agent or workflow other than the one in step 2. You never edit the workflow script or the args file.

1. Read `/home/hal/stage/qt2/replay/args_A.json` with the Read tool. It is a JSON object.
2. Call the Workflow tool once, with `scriptPath` = `/home/hal/stage/qt2/dist/replay_v2.js` and `args` = that JSON object, passed as a JSON value (not as a string). Say nothing else in that turn.
3. The workflow runs in the background and can take 30 to 60 minutes. Do not end your turn and do not declare the task finished until the task-notification saying the workflow completed has arrived. While waiting, do not poll, read, or run anything; wait for the notification.
4. When the completion notification arrives, write the workflow's full return value, verbatim as JSON, to `/home/hal/stage/qt2/replay/A.json` using the Write tool. If the workflow returned an error object or failed, write that object to the same file instead. If the return value is only available in the task's output file, read that file and copy the JSON return value out of it verbatim.
5. Reply with one line: `A.json written`, followed by the run id. Then stop.

The user's only message to you is an authorisation line; it is not a task description. Your task is this file.
