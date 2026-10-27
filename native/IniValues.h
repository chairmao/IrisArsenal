#pragma once
#include <Windows.h>
#include <cmath>
#include <cwchar>
#include <float.h>
#include <limits.h>
#include <stdexcept>
#include <string>
#include <vector>
/* 103：INI是调参数值的来源，本单元不设置业务数值的最小值/最大值，不静默钳制。
   仅启动读取；缺项/空值用原默认。动态缓冲避免把长数字截断后当作另一合法数。
   布尔/unsigned/float转换只校验对应类型，不把存储溢出、小数截断或NaN当作可用配置。
   不访问角色/世界，不保存配置文件句柄，不引入线程、锁或逐帧I/O。 */
namespace IrisIni {
inline std::string Label(const wchar_t* section,const wchar_t* key){
    return std::string(section,section+wcslen(section))+"."+std::string(key,key+wcslen(key));
}
inline double Number(const std::wstring& ini,const wchar_t* section,const wchar_t* key,double fallback){
    std::vector<wchar_t> text(64);DWORD size=0;
    for(;;){
        size=GetPrivateProfileStringW(section,key,L"",&text[0],DWORD(text.size()),ini.c_str());
        if(size<text.size()-1)break;
        // 这是Win32缓冲长度类型的表示边界，不是参数值的调参上限。
        if(text.size()>MAXDWORD/2)throw std::runtime_error("INI text cannot fit Win32 length: "+Label(section,key));
        text.resize(text.size()*2);
    }
    if(!size)return fallback;
    wchar_t* end=0;const double value=wcstod(&text[0],&end);
    if(end==&text[0]||*end||!_finite(value))throw std::runtime_error("INI requires a finite number: "+Label(section,key));
    return value;
}
inline unsigned Unsigned(double value,const char* label){
    // unsigned不能表达负数/小数；UINT_MAX是实际字段类型，不是人为配置门。
    if(!_finite(value)||value<0||value>double(UINT_MAX)||floor(value)!=value)
        throw std::runtime_error(std::string("INI requires an unsigned integer: ")+label);
    return unsigned(value);
}
inline float Float(double value,const char* label){
    if(!_finite(value)||value>double(FLT_MAX)||value<-double(FLT_MAX))
        throw std::runtime_error(std::string("INI cannot fit float: ")+label);
    const float result=float(value);
    if(value!=0&&result==0)throw std::runtime_error(std::string("INI underflows float: ")+label);
    return result;
}
inline bool Flag(const std::wstring& ini,const wchar_t* section,const wchar_t* key,bool fallback){
    const double value=Number(ini,section,key,fallback?1:0);
    if(value!=0&&value!=1)throw std::runtime_error("INI requires Boolean 0 or 1: "+Label(section,key));
    return value!=0;
}
}
