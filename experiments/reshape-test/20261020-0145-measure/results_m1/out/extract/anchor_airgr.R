# Anchor arm for measurement m1, written by run_m1.py. Do not edit by hand.
# Usage: Rscript anchor_airgr.R <path to L0123001.rda> <output json path>
# Runs airGR's own GR4J (installed on this box from the committed tarball) on three cases.
# Warm-up and initial states are the CreateRunOptions defaults. NSE is ErrorCrit_NSE on Qmm.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("usage: Rscript anchor_airgr.R <rda> <out.json>")
suppressPackageStartupMessages(library(airGR))
load(args[1L])
jnum <- function(x) {
  s <- ifelse(is.finite(x), sprintf("%.17g", x), "null")
  paste0("[", paste(s, collapse = ","), "]")
}
jone <- function(x) if (length(x) == 1L && is.finite(x)) sprintf("%.17g", x) else "null"
jstr <- function(x) paste0("\"", gsub("[\"\\\\]", "_", x), "\"")
jstrs <- function(x) paste0("[", paste(vapply(x, jstr, character(1)), collapse = ","), "]")
day_index <- function(ddmmyyyy) {
  which(format(BasinObs$DatesR, format = "%d/%m/%Y %H:%M") == paste(ddmmyyyy, "00:00"))
}
InputsModel <- CreateInputsModel(FUN_MOD = RunModel_GR4J, DatesR = BasinObs$DatesR,
                                 Precip = BasinObs$P, PotEvap = BasinObs$E)
cases <- list(
  list(id = "anchor_cal", set = "anchor", X = c(165.05, 6.46, 422.50, 2.45),
       from = "01/01/1990", to = "28/02/1990"),
  list(id = "generalist_cal", set = "generalist", X = c(291, 0.30, 109.10, 2.01),
       from = "01/01/1990", to = "28/02/1990"),
  list(id = "michel_val", set = "michel", X = c(165.05, 6.46, 422.50, 2.45),
       from = "01/03/1990", to = "31/12/1999")
)
parts <- character(0)
for (cs in cases) {
  Ind <- seq(day_index(cs$from), day_index(cs$to))
  RunOptions <- CreateRunOptions(FUN_MOD = RunModel_GR4J, InputsModel = InputsModel,
                                 IndPeriod_Run = Ind)
  InputsCrit <- CreateInputsCrit(FUN_CRIT = ErrorCrit_NSE, InputsModel = InputsModel,
                                 RunOptions = RunOptions, Obs = BasinObs$Qmm[Ind])
  OutputsModel <- RunModel_GR4J(InputsModel = InputsModel, RunOptions = RunOptions, Param = cs$X)
  OutputsCrit <- ErrorCrit_NSE(InputsCrit = InputsCrit, OutputsModel = OutputsModel, verbose = FALSE)
  wu <- RunOptions$IndPeriod_WarmUp
  wu_n <- if (identical(wu, 0L)) 0L else length(wu)
  wu_first <- if (wu_n == 0L) "none" else format(BasinObs$DatesR[wu[1L]], "%Y-%m-%d")
  parts <- c(parts, paste0(
    "{\"id\":", jstr(cs$id), ",\"set\":", jstr(cs$set), ",\"X\":", jnum(cs$X),
    ",\"warmup_n\":", wu_n, ",\"warmup_first\":", jstr(wu_first),
    ",\"ini_res_levels\":", jnum(RunOptions$IniResLevels),
    ",\"nse\":", jone(OutputsCrit$CritValue),
    ",\"crit_name\":", jstr(OutputsCrit$CritName),
    ",\"dates\":", jstrs(format(OutputsModel$DatesR, "%Y-%m-%d")),
    ",\"qsim\":", jnum(OutputsModel$Qsim),
    ",\"qobs\":", jnum(BasinObs$Qmm[Ind]), "}"))
}
writeLines(paste0("{\"r_version\":", jstr(R.version.string),
                  ",\"airgr_version\":", jstr(as.character(packageVersion("airGR"))),
                  ",\"cases\":[", paste(parts, collapse = ","), "]}"), args[2L])
cat("anchor_airgr: wrote", args[2L], "\n")
