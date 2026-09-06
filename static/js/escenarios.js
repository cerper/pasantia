document.addEventListener('DOMContentLoaded', () => {
    
    // =========================================================================
    // 1. SECCIÓN: GESTIÓN DE ESCENARIOS Y CURSOS DE ACCIÓN
    // =========================================================================
    
    // Referencias a los elementos del DOM de escenarios
    const btnAgregar = document.getElementById('btn_agregar_escenario');
    const btnLimpiar = document.getElementById('btn_limpiar_campos');
    const selectCategoria = document.getElementById('escenario_categoria');
    const inputAnalisis = document.getElementById('escenario_analisis');
    const inputAccion = document.getElementById('curso_accion');
    
    const contenedorEscenarios = document.getElementById('contenedor_escenarios');
    const sinEscenariosMsg = document.getElementById('sin_escenarios');
    const inputHidden = document.getElementById('escenarios_json');
    const formReporte = document.getElementById('form_reporte');

    // Arreglo en memoria para acumular los escenarios
    let listaEscenarios = [];

    // Función para limpiar las entradas del formulario individual de escenarios
    function limpiarEntradas() {
        if (selectCategoria) selectCategoria.value = '';
        if (inputAnalisis) inputAnalisis.value = '';
        if (inputAccion) inputAccion.value = '';
    }

    // Evento para la 'X' superior del formulario de escenarios
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', limpiarEntradas);
    }

    // Evento al hacer clic en el botón '+' para agregar escenario
    if (btnAgregar) {
        btnAgregar.addEventListener('click', () => {
            const categoria = selectCategoria ? selectCategoria.value : '';
            const analisis = inputAnalisis ? inputAnalisis.value.trim() : '';
            const accion = inputAccion ? inputAccion.value.trim() : '';

            // Validación de campos requeridos
            if (!categoria || !analisis || !accion) {
                alert('Por favor complete la categoría, el análisis y el curso de acción antes de agregar.');
                return;
            }

            // Crear el objeto del escenario
            const nuevoEscenario = {
                categoria: categoria,
                analisis: analisis,
                curso_accion: accion
            };

            // Añadir a la lista en memoria
            listaEscenarios.push(nuevoEscenario);

            // Actualizar la vista y limpiar
            renderizarListaEscenarios();
            limpiarEntradas();
        });
    }

    // Dibujar en el DOM las tarjetas de escenarios agregados
    function renderizarListaEscenarios() {
        if (!contenedorEscenarios) return;

        contenedorEscenarios.innerHTML = '';

        if (listaEscenarios.length === 0) {
            if (sinEscenariosMsg) contenedorEscenarios.appendChild(sinEscenariosMsg);
            if (inputHidden) inputHidden.value = '[]';
            return;
        }

        listaEscenarios.forEach((esc, index) => {
            const card = document.createElement('div');
            card.className = "p-3 bg-movilnet-bg border border-movilnet-input-border rounded-lg text-xs space-y-1 relative group";

            // Badge según la categoría seleccionada
            let badgeColor = "bg-gray-100 text-gray-800";
            if (esc.categoria === "Favorable") badgeColor = "bg-green-100 text-green-700";
            if (esc.categoria === "Desfavorable") badgeColor = "bg-red-100 text-red-700";
            if (esc.categoria === "Neutral") badgeColor = "bg-yellow-100 text-yellow-700";

            card.innerHTML = `
                <div class="flex items-center justify-between font-bold">
                    <span class="px-2 py-0.5 rounded text-[10px] ${badgeColor}">
                        ${esc.categoria}
                    </span>
                    <button type="button" onclick="eliminarEscenario(${index})" class="text-movilnet-muted hover:text-red-500 transition-colors" title="Eliminar escenario">
                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    </button>
                </div>
                <p class="text-movilnet-dark"><strong>Análisis:</strong> ${esc.analisis}</p>
                <p class="text-movilnet-muted"><strong>Acción:</strong> ${esc.curso_accion}</p>
            `;

            contenedorEscenarios.appendChild(card);
        });

        // Actualizar el valor del input oculto con la cadena JSON
        if (inputHidden) {
            inputHidden.value = JSON.stringify(listaEscenarios);
        }

        // Renderizar de nuevo los íconos dinámicos de Lucide
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    // Función global para eliminar un escenario de la lista
    window.eliminarEscenario = function(index) {
        listaEscenarios.splice(index, 1);
        renderizarListaEscenarios();
    };

    // Sincronizar JSON antes de enviar el formulario
    if (formReporte) {
        formReporte.addEventListener('submit', () => {
            if (inputHidden) {
                inputHidden.value = JSON.stringify(listaEscenarios);
            }
        });
    }


    // =========================================================================
    // 2. SECCIÓN: VISTA PREVIA DE IMÁGENES
    // =========================================================================

    /**
     * Función reutilizable para precargar vistas previas de imágenes
     * @param {string} inputId - ID del input file
     * @param {string} labelId - ID del label/contenedor de subida
     * @param {string} previewContainerId - ID del contenedor de la vista previa
    
     */
    function setupImagePreview(inputId, labelId, previewContainerId,) {
        const input = document.getElementById(inputId);
        const label = document.getElementById(labelId);
        const previewContainer = document.getElementById(previewContainerId);

        if (!input || !previewContainer) return;

        input.addEventListener('change', () => {
            const archivos = Array.from(input.files).filter((file) => file.type.startsWith('image/'));
            previewContainer.innerHTML = '';

            archivos.forEach((archivo, index) => {
                const lector = new FileReader();
                const item = document.createElement('div');
                item.className = 'relative';
                const imagen = document.createElement('img');
                imagen.alt = `Vista previa ${index + 1}`;
                imagen.className = 'w-full h-48 object-cover rounded-lg';
                const eliminar = document.createElement('button');
                eliminar.type = 'button';
                eliminar.title = 'Eliminar imagen';
                eliminar.className = 'absolute top-2 right-2 bg-movilnet-dark/70 hover:bg-red-500 text-white p-1 rounded-full transition-colors shadow-sm';
                eliminar.innerHTML = '<i data-lucide="x" class="w-4 h-4"></i>';
                eliminar.addEventListener('click', () => {
                    archivos.splice(index, 1);
                    const transferencia = new DataTransfer();
                    archivos.forEach((archivoRestante) => transferencia.items.add(archivoRestante));
                    input.files = transferencia.files;
                    input.dispatchEvent(new Event('change'));
                });
                item.append(imagen, eliminar);
                previewContainer.appendChild(item);
                lector.onload = (event) => { imagen.src = event.target.result; };
                lector.readAsDataURL(archivo);
            });

            const tieneImagenes = archivos.length > 0;
            if (label) label.classList.toggle('hidden', tieneImagenes);
            previewContainer.classList.toggle('hidden', !tieneImagenes);
            if (window.lucide) lucide.createIcons();
        });
    }

    function setupNoCampaign(checkboxId, inputIds, labelIds, previewIds) {
        const checkbox = document.getElementById(checkboxId);
        if (!checkbox) return;

        checkbox.addEventListener('change', () => {
            inputIds.forEach((id, index) => {
                const input = document.getElementById(id);
                const label = document.getElementById(labelIds[index]);
                const preview = document.getElementById(previewIds[index]);
                if (checkbox.checked) {
                    input.value = '';
                    input.disabled = true;
                    label.classList.add('hidden');
                    preview.classList.add('hidden');
                } else {
                    input.disabled = false;
                    label.classList.remove('hidden');
                }
            });
        });
    }

    // Configuraciones de vista previa para cada input de imagen en el reporte:
    
    // 1. Campaña Movistar - Imágenes
    setupImagePreview(
        'campana_movistar_imagenes',
        'label_movistar',
        'preview_container_movistar',
        'preview_img_movistar',
        'btn_remove_movistar'
    );

    setupNoCampaign(
        'no_campana_movistar',
        ['campana_movistar_imagenes', 'campana_movistar_metrica_imagen'],
        ['label_movistar', 'label_movistar_metrica'],
        ['preview_container_movistar', 'preview_container_movistar_metrica']
    );

    setupNoCampaign(
        'no_campana_digitel',
        ['campana_digitel_imagenes', 'campana_digitel_metrica_imagen'],
        ['label_digitel', 'label_digitel_metrica'],
        ['preview_container_digitel', 'preview_container_digitel_metrica']
    );

    // 2. Campaña Movistar - Métrica/Sentimiento
    setupImagePreview(
        'campana_movistar_metrica_imagen',
        'label_movistar_metrica',
        'preview_container_movistar_metrica',
        'preview_img_movistar_metrica',
        'btn_remove_movistar_metrica'
    );

    // 3. Campaña Digitel - Imágenes
    setupImagePreview(
        'campana_digitel_imagenes',
        'label_digitel',
        'preview_container_digitel',
        'preview_img_digitel',
        'btn_remove_digitel'
    );

    // 4. Campaña Digitel - Métrica/Sentimiento
    setupImagePreview(
        'campana_digitel_metrica_imagen',
        'label_digitel_metrica',
        'preview_container_digitel_metrica',
        'preview_img_digitel_metrica',
        'btn_remove_digitel_metrica'
    );

});