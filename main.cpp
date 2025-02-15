#include"bits/stdc++.h"
#include<unistd.h>

#define int long long
//#define double long double
#define ii pair <int,int>
#define fi first
#define se second
#define endl '\n'
#define all(x) x.begin(), x.end()
#define rall(x) x.rbegin(), x.rend()
using namespace std;

signed main(){
    //freopen("input.INP", "r", stdin);
    //freopen("output.OUT", "w", stdout);
    if (fopen(".inp", "r")) {
        freopen(".inp", "r", stdin);
        freopen(".out", "w", stdout);
    }
    cout << "Hệ thống AI kiểm soát ra vào trường học bằng nhận diện họ và tên tự động, được tạo bởi Orzlab" << endl;
    cout << "Automated School Access Control System Using AI Name Recognition" << endl;
    cout << "Hãy nhập tên học sinh: ";
    string s;
    getline(cin, s);
    for (int i = 0; i <= 20; i++){
        cout << "Đang xử lý " << i * 5 << "%" << endl;
        usleep(1000000);
    }
    cout << "Đã nhập diện được học sinh " << s;
    return 0;
}