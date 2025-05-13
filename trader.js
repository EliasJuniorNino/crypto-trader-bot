const { exec } = require('child_process');
const { assert } = require('console');

async function generatePredict() {
    await new Promise((resolve, reject) => {
        exec('node scripts/miner/get_fear_alternative.me.js', (error, stdout, stderr) => {
            if (error) {
              console.error(`Erro ao executar o script: ${error.message}`);
            }
            if (stderr) {
              console.error(`stderr: ${stderr}`);
            }
            console.log(`stdout: ${stdout}`);
            resolve()
          });
    })
    await new Promise((resolve, reject) => {
        exec('node scripts/miner/get_fear_coinmarketcap.js', (error, stdout, stderr) => {
          if (error) {
            console.error(`Erro ao executar o script: ${error.message}`);
          }
          if (stderr) {
            console.error(`stderr: ${stderr}`);
          }
          console.log(`stdout: ${stdout}`);
          resolve()
          });
    })
    await new Promise((resolve, reject) => {
        exec('node scripts/miner/get_binance_CurrentDayCryptosHistory.js', (error, stdout, stderr) => {
            if (error) {
              console.error(`Erro ao executar o script: ${error.message}`);
            }
            if (stderr) {
              console.error(`stderr: ${stderr}`);
            }
            console.log(`stdout: ${stdout}`);
            resolve()
          });
    })
    await new Promise((resolve, reject) => {
        exec('node scripts/miner/generate_dataset.js', (error, stdout, stderr) => {
          if (error) {
            console.error(`Erro ao executar o script: ${error.message}`);
          }
          if (stderr) {
            console.error(`stderr: ${stderr}`);
          }
          console.log(`stdout: ${stdout}`);
          resolve()
          });
    })
    await new Promise((resolve, reject) => {
        exec('python scripts/trader_strategies/predict_rf.py', (error, stdout, stderr) => {
          if (error) {
            console.error(`Erro ao executar o script: ${error.message}`);
          }
          if (stderr) {
            console.error(`stderr: ${stderr}`);
          }
          console.log(`stdout: ${stdout}`);
          resolve()
          });
    })
}

async function main() {
  while(true) {
    try {
      await generatePredict()
      await new Promise((resolve, _) => setTimeout(resolve, 60*60*24))
    } catch (e) {
      console.error(e)
    }
  }
}

main()