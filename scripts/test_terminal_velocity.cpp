#include <ego_planner/terminal_velocity.h>
#include <cassert>
int main() {
  using ego_planner::terminalStartVelocity;
  assert(terminalStartVelocity(Eigen::Vector3d(-.014,.002,0),.025).norm()==0);
  Eigen::Vector3d moving(-.1,.02,0);
  assert((terminalStartVelocity(moving,.025)-moving).norm()==0);
  assert(terminalStartVelocity(Eigen::Vector3d(.025,0,0),.025).x()==.025);
  assert(terminalStartVelocity(Eigen::Vector3d(.001,0,0),0).x()==.001);
}
