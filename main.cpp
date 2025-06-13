#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#endif

#include "src/Application.hpp"

int main(const int argc, char *argv[])
{
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    _setmode(_fileno(stdout), _O_TEXT); // _O_U8TEXT se usar std::wcout
#endif

    std::unordered_map<std::string, std::string> params;
    sqlite3 *db;

    const char *database_filename = getAppConfig("database", "filename").c_str();
    if (const int rc = sqlite3_open(database_filename, &db); rc != SQLITE_OK)
    {
        std::cerr << "Erro ao abrir o banco: " << sqlite3_errmsg(db) << std::endl;
        return 1;
    }

    for (int i = 0; i < argc; ++i)
    {
        std::string key = argv[i];
        std::string value;

        if (key.empty() || key[0] != '-')
        {
            continue;
        }

        if (i + 1 < argc && !(std::string(argv[i + 1]).size() > 0 && std::string(argv[i + 1])[0] == '-'))
        {
            value = argv[i + 1];
            ++i;
        }
        else
        {
            value = "1";
        }

        params[key] = value;
    }

    Application::Run(params, db);

    sqlite3_close(db);

    return 0;
}