function openModal(imgPath) {
    const modal = document.getElementById("screenshotModal");
    const modalImg = document.getElementById("modalImg");
    modal.style.display = "block";
    modalImg.src = imgPath;
}

function closeModal() {
    document.getElementById("screenshotModal").style.display = "none";
}

window.onclick = function(event) {
    const modal = document.getElementById("screenshotModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

let currentSortColumn = 0;
let currentSortDirection = 'asc';

function sortTable(columnIndex) {
    const table = document.querySelector('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const headers = table.querySelectorAll('th');
    
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortDirection = 'asc';
        currentSortColumn = columnIndex;
    }
    
    headers.forEach((header, index) => {
        header.classList.remove('sort-asc', 'sort-desc');
        
        if (index === columnIndex) {
            header.classList.add(`sort-${currentSortDirection}`);
        }
    });
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (columnIndex === 1) {
            return currentSortDirection === 'asc' 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        }
        
        if (columnIndex === 2) {
            const aPrice = parseFloat(aValue.replace(/[^0-9.]/g, '')) || 0;
            const bPrice = parseFloat(bValue.replace(/[^0-9.]/g, '')) || 0;
            
            return currentSortDirection === 'asc' 
                ? aPrice - bPrice 
                : bPrice - aPrice;
        }
        
        return currentSortDirection === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

document.addEventListener('DOMContentLoaded', function() {
    const table = document.querySelector('table');
    const headers = table.querySelectorAll('th');
    
    headers.forEach((header, index) => {
        header.addEventListener('click', () => sortTable(index));
        header.classList.add('sortable');
    });
}); 