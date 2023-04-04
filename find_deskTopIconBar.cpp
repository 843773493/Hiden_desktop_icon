#include <windows.h>

extern "C" __declspec(dllexport) HWND GetDesktopListViewHWND()
{
    HWND hWorkerW = NULL;
    HWND hShellViewWin = NULL;
    HWND hDefView = NULL;
    HWND hDesktopListView = NULL;

    // ��ȡ WorkerW ����
    while ((hWorkerW = FindWindowEx(NULL, hWorkerW, L"WorkerW", NULL)) != NULL)
    {
        hShellViewWin = FindWindowEx(hWorkerW, NULL, L"SHELLDLL_DefView", NULL);
        if (hShellViewWin != NULL)
        {
            hDefView = FindWindowEx(hShellViewWin, NULL, L"SysListView32", L"FolderView");
            if (hDefView != NULL)
                break;
        }
    }

    if (hDefView == NULL)
    {
        // ���δ�ҵ� WorkerW ���ڣ����Բ��� Progman ����
        HWND progman = FindWindow(L"Progman", NULL);
        hDefView = FindWindowEx(progman, NULL, L"SHELLDLL_DefView", NULL);
        if (hDefView != NULL)
            hDesktopListView = FindWindowEx(hDefView, NULL, L"SysListView32", L"FolderView");
    }
    else
        hDesktopListView = hDefView;

    return hDesktopListView;
}

extern "C" __declspec(dllexport) void ShowDesktopIcons(BOOL show)
{
    HWND desktophwnd = GetDesktopListViewHWND();
    ShowWindow(desktophwnd, show ? SW_SHOW : SW_HIDE);
}

