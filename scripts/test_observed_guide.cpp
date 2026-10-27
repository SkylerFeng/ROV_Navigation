#include "../ros_ws/src/plan_manage/include/ego_planner/observed_guide.h"
#include <cassert>
#include <iostream>
using Eigen::Vector3d;
int main() {
  auto free=[](const Vector3d &p) {return std::abs(p.x())>.2 || std::abs(p.y())>.7;};
  Vector3d start(-1,0,1),goal(1,0,1);
  auto route=ego_planner::observedGuide(start,goal,free);
  assert(!route.empty() && (route.back()-goal).norm()<1e-8);
  Vector3d previous=start;
  for(const auto &p:route) {
    assert(std::abs(p.z()-1)<1e-8);
    for(int i=0;i<=100;++i) assert(free(previous+(p-previous)*(double(i)/100)));
    previous=p;
  }
  auto wall=[](const Vector3d &p) {return std::abs(p.x())>.2;};
  assert(ego_planner::observedGuide(start,goal,wall).empty());
  assert(ego_planner::observedGuide(Vector3d(0,0,1),goal,free).empty());
  auto clear=[](const Vector3d&) {return true;};
  auto direct=ego_planner::observedGuide(start,goal,clear);
  assert(direct.size()==1 && (direct.front()-goal).norm()<1e-8);
  std::cout << "Passed: planar detour, collision-free segments, blocked start, disconnected map, direct route\n";
}
