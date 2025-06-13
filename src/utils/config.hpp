#pragma once

#include <fstream>
#include <string>
#include <stdexcept>

inline void createDefaultIni(const std::string &iniPath)
{
    std::ofstream file(iniPath);
    if (!file.is_open())
    {
        throw std::runtime_error("Não conseguiu criar o arquivo INI: " + iniPath);
    }

    // Conteúdo padrão inicial do arquivo INI — ajuste conforme sua necessidade
    file << "[database]\n"
            "filename=database.db\n"
            "data_dir=data";
    file.close();
}

inline std::string getAppConfig(const std::string &section, const std::string &key)
{
    const std::string iniPath = "config.ini"; // caminho relativo ao executável

    std::ifstream file(iniPath);
    if (!file.is_open())
    {
        // Se arquivo não existe, cria com conteúdo padrão
        createDefaultIni(iniPath);
        // Agora tenta abrir novamente
        file.open(iniPath);
        if (!file.is_open())
        {
            throw std::runtime_error("Não conseguiu abrir o arquivo INI nem após criação: " + iniPath);
        }
    }

    std::string line;
    bool inTargetSection = false;
    while (std::getline(file, line))
    {
        // Remove espaços no começo e fim
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        if (line.empty() || line[0] == ';' || line[0] == '#')
            continue; // pula comentários e linhas vazias

        if (line.front() == '[' && line.back() == ']')
        {
            std::string currentSection = line.substr(1, line.length() - 2);
            inTargetSection = (currentSection == section);
            continue;
        }

        if (inTargetSection)
        {
            auto pos = line.find('=');
            if (pos != std::string::npos)
            {
                std::string k = line.substr(0, pos);
                std::string v = line.substr(pos + 1);

                // Trim
                k.erase(0, k.find_first_not_of(" \t\r\n"));
                k.erase(k.find_last_not_of(" \t\r\n") + 1);
                v.erase(0, v.find_first_not_of(" \t\r\n"));
                v.erase(v.find_last_not_of(" \t\r\n") + 1);

                if (k == key)
                {
                    return v;
                }
            }
        }
    }

    throw std::runtime_error("Chave '" + key + "' não encontrada na seção [" + section + "]");
}
