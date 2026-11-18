#pragma once
#include <Eigen/Core>
namespace ego_planner {
// A nearly stationary station-keeping residual is not a new path direction.
// Preserve measured velocity above the explicitly configured low-speed band.
inline Eigen::Vector3d terminalStartVelocity(const Eigen::Vector3d &velocity,double deadband) {
  return velocity.norm()<deadband ? Eigen::Vector3d::Zero().eval() : velocity;
}
}
