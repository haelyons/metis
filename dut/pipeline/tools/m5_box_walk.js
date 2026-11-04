'use strict'
// Fixture walks of the fake box tree (probe replacement, profiler replacement) run right after
// bin/box starts a detached job, which may meanwhile remove or rename files and directories
// (temporary files, `rm -rf out/...`, mktemp). An entry that disappears between listing and
// reading (ENOENT), or a directory replaced by a file (ENOTDIR), is skipped; every other error
// is thrown as before.
const fs = require('node:fs')

const vanished = error => error?.code === 'ENOENT' || error?.code === 'ENOTDIR'
function unlessVanished(read) {
  try { return read() } catch (error) { if (vanished(error)) return undefined; throw error }
}
// Directory entries, or [] if the directory is gone.
const entries = directory => unlessVanished(() => fs.readdirSync(directory, { withFileTypes: true })) ?? []
// File text, or undefined if the file is gone.
const text = file => unlessVanished(() => fs.readFileSync(file, 'utf8'))

module.exports = { vanished, entries, text }
