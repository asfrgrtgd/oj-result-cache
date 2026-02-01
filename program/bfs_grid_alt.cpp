#include <bits/stdc++.h>
using namespace std;

int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int h,w; if(!(cin>>h>>w)) return 0;
    vector<string> grid(h); for(int i=0;i<h;i++) cin>>grid[i];

    pair<int,int> s{-1,-1}, t{-1,-1};
    for(int i=0;i<h;i++){
        for(int j=0;j<w;j++){
            if(grid[i][j]=='S') s={i,j};
            if(grid[i][j]=='G') t={i,j};
        }
    }

    const int INF=1e9;
    vector<vector<int>> dist(h, vector<int>(w, INF));
    queue<pair<int,int>> q; dist[s.first][s.second]=0; q.push(s);

    int dx[4]={1,-1,0,0}; int dy[4]={0,0,1,-1};
    while(!q.empty()){
        auto [x,y]=q.front(); q.pop();
        for(int k=0;k<4;k++){
            int nx=x+dx[k]; int ny=y+dy[k];
            if(nx<0||nx>=h||ny<0||ny>=w) continue;
            if(grid[nx][ny]=='#') continue; // wall
            if(dist[nx][ny]!=INF) continue;
            dist[nx][ny]=dist[x][y]+1; q.push({nx,ny});
        }
    }

    int ans=dist[t.first][t.second];
    if(ans==INF) cout<<-1<<"\n"; else cout<<ans<<"\n";
    return 0;
}
