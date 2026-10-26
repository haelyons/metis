#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <ctime>
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <unistd.h>
static pthread_mutex_t timing_lock = PTHREAD_MUTEX_INITIALIZER;
static void record_output(const char *text) {
  const char *path = getenv("MC_PHASE_OUT");
  if (!path) return;
  timespec ts{};
  clock_gettime(CLOCK_MONOTONIC, &ts);
  char line[16384];
  int prefix = snprintf(line, sizeof(line), "%.17g\t", ts.tv_sec + ts.tv_nsec * 1e-9);
  size_t n = (size_t)prefix;
  for (const char *c = text; *c && n + 2 < sizeof(line); ++c)
    line[n++] = (*c == '\n' || *c == '\r' || *c == '\t') ? ' ' : *c;
  line[n++] = '\n';
  pthread_mutex_lock(&timing_lock);
  int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
  if (fd >= 0) {
    size_t done = 0;
    while (done < n) {
      ssize_t wrote = write(fd, line + done, n - done);
      if (wrote <= 0) break;
      done += (size_t)wrote;
    }
    close(fd);
  }
  pthread_mutex_unlock(&timing_lock);
}
static void record_format(const char *format, va_list args) {
  char text[16384];
  va_list copy;
  va_copy(copy, args);
  vsnprintf(text, sizeof(text), format, copy);
  va_end(copy);
  record_output(text);
}
extern "C" int printf(const char *format, ...) {
  using Function = int (*)(FILE *, const char *, va_list);
  static Function real = (Function)dlsym(RTLD_NEXT, "vfprintf");
  va_list args;
  va_start(args, format);
  record_format(format, args);
  int result = real(stdout, format, args);
  va_end(args);
  return result;
}
extern "C" int __printf_chk(int flag, const char *format, ...) {
  using Function = int (*)(FILE *, int, const char *, va_list);
  static Function real = (Function)dlsym(RTLD_NEXT, "__vfprintf_chk");
  va_list args;
  va_start(args, format);
  record_format(format, args);
  int result = real(stdout, flag, format, args);
  va_end(args);
  return result;
}
extern "C" int puts(const char *text) {
  using Function = int (*)(const char *);
  static Function real = (Function)dlsym(RTLD_NEXT, "puts");
  record_output(text);
  return real(text);
}
