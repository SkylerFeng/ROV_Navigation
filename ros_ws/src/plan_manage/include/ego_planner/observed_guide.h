#pragma once
#include <Eigen/Eigen>
#include <functional>
#include <queue>
#include <limits>
#include <algorithm>
#include <vector>
#include <cmath>

namespace ego_planner {
// Fixed-height guide from observed inflated occupancy, not scene obstacles.
inline std::vector<Eigen::Vector3d> observedGuide(
    const Eigen::Vector3d &start, const Eigen::Vector3d &goal,
    const std::function<bool(const Eigen::Vector3d&)> &free)
{
  constexpr int nx=161, ny=121, cx=80, cy=60;
  constexpr double step=.1;
  auto point=[&](int id) { return Eigen::Vector3d(start.x()+(id%nx-cx)*step,
      start.y()+(id/nx-cy)*step, start.z()); };
  auto segment=[&](const Eigen::Vector3d &a,const Eigen::Vector3d &b,bool margin) {
    int n=std::max(1,int(std::ceil((b-a).norm()/.025)));
    for(int i=0;i<=n;++i) {
      Eigen::Vector3d p=a+(b-a)*(double(i)/n);
      if(!free(p)) return false;
      if(margin && (p-start).norm()>.2 && (p-goal).norm()>.2)
        for(const Eigen::Vector3d &d : {Eigen::Vector3d(.1,0,0),Eigen::Vector3d(-.1,0,0),
                                      Eigen::Vector3d(0,.1,0),Eigen::Vector3d(0,-.1,0)})
          if(!free(p+d)) return false;
    }
    return true;
  };
  if(!free(start)||!free(goal)) return {};
  if(segment(start,goal,true)) return {goal};
  int gx=cx+int(std::round((goal.x()-start.x())/step));
  int gy=cy+int(std::round((goal.y()-start.y())/step));
  if(gx<0||gx>=nx||gy<0||gy>=ny) return {};
  int source=cy*nx+cx, target=gy*nx+gx;
  if(!segment(point(target),goal,false)) return {};
  std::vector<double> dist(nx*ny,std::numeric_limits<double>::infinity());
  std::vector<int> parent(nx*ny,-1);
  std::vector<signed char> occupancy(nx*ny,-1),closed(nx*ny,0);
  auto available=[&](int id) {
    if(occupancy[id]<0) occupancy[id]=free(point(id))?1:0;
    return occupancy[id]==1;
  };
  using Entry=std::pair<double,int>;
  std::priority_queue<Entry,std::vector<Entry>,std::greater<Entry>> queue;
  dist[source]=0;queue.push({(goal-start).norm(),source});
  while(!queue.empty()) {
    int id=queue.top().second;queue.pop();
    if(closed[id]) continue;
    closed[id]=1;
    if(id==target) break;
    int x=id%nx,y=id/nx;
    for(int dx=-1;dx<=1;++dx) for(int dy=-1;dy<=1;++dy) {
      if((dx==0&&dy==0)||x+dx<0||x+dx>=nx||y+dy<0||y+dy>=ny) continue;
      int next=(y+dy)*nx+x+dx;
      if(closed[next]||!available(next)) continue;
      if(!segment(point(id),point(next),false)) continue;
      bool near=false;
      for(int ox=-2;ox<=2&&!near;ox+=2) for(int oy=-2;oy<=2;oy+=2) {
        int xx=x+dx+ox,yy=y+dy+oy;
        if(xx<0||xx>=nx||yy<0||yy>=ny||!available(yy*nx+xx)) {near=true;break;}
      }
      double cost=dist[id]+step*std::hypot(dx,dy)*(near?4.:1.);
      if(cost<dist[next]) {dist[next]=cost;parent[next]=id;
        queue.push({cost+(goal-point(next)).norm(),next});}
    }
  }
  if(!closed[target]) return {};
  std::vector<Eigen::Vector3d> raw;
  for(int id=target;id!=-1;id=parent[id]) raw.push_back(point(id));
  std::reverse(raw.begin(),raw.end());raw.push_back(goal);
  std::vector<Eigen::Vector3d> result;
  size_t i=0;
  while(i+1<raw.size()) {
    size_t next=i+1;
    for(size_t j=i+2;j<raw.size();++j) {
      if((raw[j]-raw[i]).norm()>.8) break;
      if(segment(raw[i],raw[j],true)) next=j;
    }
    result.push_back(raw[next]);i=next;
  }
  return result;
}
}
