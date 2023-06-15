let file, fileId, fileName, fileSize, chunksTotal
const CHUNK_SIZE = 5 * 1024 * 1024

const input = document.getElementById("input")

const handleChange = (event) => {
    file = event.target.files[0]
    fileId = crypto.randomUUID()
    fileName = file.name
    fileSize = file.size
    chunksTotal = Math.ceil(fileSize / CHUNK_SIZE)
}

input.addEventListener("change", handleChange)

const createChunk = (file, index) => {
    const isLastChunk = index + 1 == chunksTotal;

    let chunk;
    if (isLastChunk) {
      chunk = file.slice(index * CHUNK_SIZE);
    } else {
      chunk = file.slice(index * CHUNK_SIZE, (index + 1) * CHUNK_SIZE);
    }

    const chunkForm = new FormData();
    const chunkName = fileName + '.chunk' + index;
    chunkForm.append('chunk', chunk, chunkName);
    chunkForm.append('chunkIndex', index.toString());
    chunkForm.append('chunkSize', chunk.size.toString());
    chunkForm.append('chunksTotal', chunksTotal.toString());
    chunkForm.append('fileId', fileId);
    chunkForm.append('fileName', fileName);
    chunkForm.append('fileSize', fileSize.toString());

    return chunkForm;
};
