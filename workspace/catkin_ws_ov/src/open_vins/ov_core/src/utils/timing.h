/*
 * OpenVINS: An Open Platform for Visual-Inertial Research
 * Scoped Timer Infrastructure — header-only
 *
 * Adds lightweight per-stage timing to the VIO pipeline.
 * Thread-safe: multiple threads can log concurrently.
 * Output CSV: frame_id, module, thread_id, start_ns, end_ns, duration_ms
 */

#ifndef OV_CORE_TIMING_H
#define OV_CORE_TIMING_H

#include <chrono>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace ov_core {

/**
 * @brief Thread-safe singleton logger for pipeline timing events.
 *
 * Call TimingLogger::instance().open("/path/to/ov_timing.csv") once at startup.
 * Each ScopedTimer writes one row on destruction.
 */
class TimingLogger {
public:
  struct Entry {
    int64_t frame_id;
    std::string module;
    uint64_t thread_id;
    int64_t start_ns;
    int64_t end_ns;
  };

  static TimingLogger &instance() {
    static TimingLogger inst;
    return inst;
  }

  /// Open the output CSV (call once from VioManager constructor)
  void open(const std::string &path) {
    std::lock_guard<std::mutex> lk(mtx_);
    if (ofs_.is_open())
      ofs_.close();
    ofs_.open(path, std::ios::out | std::ios::trunc);
    if (ofs_.is_open()) {
      ofs_ << "frame_id,module,thread_id,start_ns,end_ns,duration_ms\n";
      ofs_.flush();
      enabled_ = true;
    }
  }

  bool enabled() const { return enabled_; }

  /// Called by ScopedTimer on destruction
  void record(const Entry &e) {
    if (!enabled_)
      return;
    double dur_ms = (e.end_ns - e.start_ns) * 1e-6;
    std::lock_guard<std::mutex> lk(mtx_);
    ofs_ << e.frame_id << "," << e.module << "," << e.thread_id << "," << e.start_ns << "," << e.end_ns << ","
         << std::fixed << std::setprecision(4) << dur_ms << "\n";
    ofs_.flush();
  }

  ~TimingLogger() {
    if (ofs_.is_open())
      ofs_.close();
  }

private:
  TimingLogger() = default;
  std::mutex mtx_;
  std::ofstream ofs_;
  bool enabled_ = false;
};

/**
 * @brief RAII scoped timer. Records start/end nanoseconds and thread ID.
 *
 * Usage:
 *   {
 *     auto _t = ov_core::ScopedTimer("feature_tracking", frame_id_);
 *     trackFEATS->feed_new_camera(message);
 *   }  // ← timer stops and logs here automatically
 */
class ScopedTimer {
public:
  ScopedTimer(const std::string &module, int64_t frame_id) : module_(module), frame_id_(frame_id) {
    start_ns_ = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
    // capture thread id as uint64
    std::ostringstream oss;
    oss << std::this_thread::get_id();
    thread_id_ = std::stoull(oss.str());
  }

  ~ScopedTimer() {
    int64_t end_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
    TimingLogger::instance().record({frame_id_, module_, thread_id_, start_ns_, end_ns});
  }

  // Non-copyable, non-movable
  ScopedTimer(const ScopedTimer &) = delete;
  ScopedTimer &operator=(const ScopedTimer &) = delete;

private:
  std::string module_;
  int64_t frame_id_;
  int64_t start_ns_;
  uint64_t thread_id_;
};

} // namespace ov_core

#endif // OV_CORE_TIMING_H
