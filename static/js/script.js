document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dropZone = fileInput.closest('.drop-zone');
    const promptElement = dropZone.querySelector('.drop-zone__prompt');
    const statusElement = dropZone.querySelector('.drop-zone__status');
    const browseBtn = dropZone.querySelector('.btn-browse');

    // Função para atualizar a aparência da drop zone com o nome do arquivo
    const updateStatus = (file) => {
        if (file) {
            // Esconde o prompt inicial e mostra o status
            promptElement.style.display = 'none';
            statusElement.style.display = 'block';
            statusElement.textContent = `Arquivo selecionado: ${file.name}`;
        } else {
            // Restaura ao estado original
            promptElement.style.display = 'flex'; // Usamos flex para centralizar
            statusElement.style.display = 'none';
            statusElement.textContent = '';
        }
    };

    // Abre o seletor de arquivos ao clicar no botão "Selecione"
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Abre o seletor de arquivos ao clicar na drop zone
    dropZone.addEventListener('click', (e) => {
        // Impede que o clique no botão dispare este evento também
        if (!browseBtn.contains(e.target)) {
            fileInput.click();
        }
    });

    // Atualiza o status quando um arquivo é escolhido pelo seletor
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            updateStatus(fileInput.files[0]);
        }
    });

    // --- Lógica do Drag and Drop ---

    // Adiciona a classe de feedback visual quando um arquivo é arrastado sobre a zona
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault(); // Necessário para permitir o drop
        dropZone.classList.add('drop-zone--over');
    });

    // Remove a classe de feedback visual quando o arquivo sai da zona
    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('drop-zone--over');
        });
    });

    // Processa o arquivo quando ele é solto na zona
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        
        // Verifica se algum arquivo foi solto
        if (e.dataTransfer.files.length > 0) {
            const droppedFile = e.dataTransfer.files[0];

            // Valida se o arquivo é .csv
            if (droppedFile.name.endsWith('.csv')) {
                fileInput.files = e.dataTransfer.files; // Associa o arquivo ao input
                updateStatus(droppedFile);
            } else {
                alert('Por favor, envie apenas arquivos no formato .csv');
            }
        }
        
        dropZone.classList.remove('drop-zone--over');
    });

});