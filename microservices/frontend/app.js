const outputEl = document.getElementById("output");
const statusEl = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const todoFormEl = document.getElementById("todoForm");
const titleInputEl = document.getElementById("titleInput");
const descriptionInputEl = document.getElementById("descriptionInput");
const todoListEl = document.getElementById("todoList");
const todoStatusEl = document.getElementById("todoStatus");
const reloadTodosBtn = document.getElementById("reloadTodosBtn");

const API_ROUTE = "/api/machine-info";
const TODOS_ROUTE = "/api/todos";
const RAW_API_BASE_URL = (window.APP_CONFIG?.API_URL || "").trim();

function resolveApiBaseUrl(value) {
  if (!value) {
    return "";
  }

  const trimmed = value.replace(/\/+$/, "");

  try {
    const parsed = new URL(trimmed, window.location.origin);

    // `haproxy` is a Docker-internal DNS name, not reachable from the browser.
    if (parsed.hostname === "haproxy") {
      return window.location.origin;
    }
  } catch (_error) {
    return trimmed;
  }

  return trimmed;
}

const API_BASE_URL = resolveApiBaseUrl(RAW_API_BASE_URL);
const BASE_PATH = API_BASE_URL ? API_BASE_URL.replace(/\/+$/, "") : "";
const API_URL = BASE_PATH ? `${BASE_PATH}${API_ROUTE}` : API_ROUTE;
const TODOS_URL = BASE_PATH ? `${BASE_PATH}${TODOS_ROUTE}` : TODOS_ROUTE;

async function loadMachineInfo() {
  statusEl.classList.remove("error");
  statusEl.textContent = "Chargement...";

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    outputEl.textContent = JSON.stringify(data, null, 2);
    statusEl.textContent = "OK";
  } catch (error) {
    statusEl.classList.add("error");
    statusEl.textContent = `Erreur: ${error.message}`;
    outputEl.textContent = "Impossible de recuperer la reponse du backend.";
  }
}

function setTodoStatus(message, isError = false) {
  todoStatusEl.classList.toggle("error", isError);
  todoStatusEl.textContent = message;
}

function todoItemTemplate(todo) {
  const li = document.createElement("li");
  li.className = "todo-item";
  li.dataset.id = String(todo.id);

  const main = document.createElement("div");
  main.className = "todo-main";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = Boolean(todo.done);
  checkbox.setAttribute("aria-label", "Marquer termine");
  checkbox.addEventListener("change", async () => {
    await updateTodo(todo.id, { done: checkbox.checked });
  });

  const textBlock = document.createElement("div");
  textBlock.className = "todo-text";

  const actions = document.createElement("div");
  actions.className = "todo-actions";

  const editButton = document.createElement("button");
  editButton.type = "button";
  editButton.textContent = "Modifier";
  let isEditing = false;
  let editTitleInput = null;
  let editDescriptionInput = null;

  function renderReadMode() {
    isEditing = false;
    textBlock.innerHTML = "";
    actions.innerHTML = "";

    const title = document.createElement("h3");
    title.textContent = todo.title;
    if (todo.done) {
      title.classList.add("done");
    }

    const description = document.createElement("p");
    description.textContent = todo.description || "(Sans description)";

    textBlock.appendChild(title);
    textBlock.appendChild(description);
    actions.appendChild(editButton);
    actions.appendChild(deleteButton);
  }

  function renderEditMode() {
    isEditing = true;
    textBlock.innerHTML = "";
    actions.innerHTML = "";

    editTitleInput = document.createElement("input");
    editTitleInput.type = "text";
    editTitleInput.maxLength = 200;
    editTitleInput.value = todo.title;
    editTitleInput.className = "todo-edit-input";

    editDescriptionInput = document.createElement("input");
    editDescriptionInput.type = "text";
    editDescriptionInput.maxLength = 1000;
    editDescriptionInput.value = todo.description || "";
    editDescriptionInput.className = "todo-edit-input";

    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "secondary";
    saveButton.textContent = "Enregistrer";
    saveButton.addEventListener("click", async () => {
      const newTitle = editTitleInput.value.trim();
      const newDescription = editDescriptionInput.value.trim();
      if (!newTitle) {
        setTodoStatus("Le titre est obligatoire.", true);
        return;
      }
      await updateTodo(todo.id, {
        title: newTitle,
        description: newDescription || null,
      });
    });

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "secondary";
    cancelButton.textContent = "Annuler";
    cancelButton.addEventListener("click", () => {
      renderReadMode();
    });

    textBlock.appendChild(editTitleInput);
    textBlock.appendChild(editDescriptionInput);
    actions.appendChild(saveButton);
    actions.appendChild(cancelButton);
    actions.appendChild(deleteButton);
  }

  editButton.addEventListener("click", () => {
    if (!isEditing) {
      renderEditMode();
    }
  });

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "danger";
  deleteButton.textContent = "Supprimer";
  deleteButton.addEventListener("click", async () => {
    const confirmed = window.confirm("Supprimer ce todo ?");
    if (!confirmed) {
      return;
    }
    await deleteTodo(todo.id);
  });

  actions.appendChild(editButton);
  actions.appendChild(deleteButton);

  main.appendChild(checkbox);
  main.appendChild(textBlock);
  main.appendChild(actions);
  li.appendChild(main);
  renderReadMode();
  return li;
}

async function loadTodos() {
  setTodoStatus("Chargement...");
  try {
    const response = await fetch(TODOS_URL);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const todos = await response.json();
    todoListEl.innerHTML = "";
    todos.forEach((todo) => todoListEl.appendChild(todoItemTemplate(todo)));
    setTodoStatus(`OK (${todos.length})`);
  } catch (error) {
    setTodoStatus(`Erreur: ${error.message}`, true);
    todoListEl.innerHTML = "";
  }
}

async function createTodo(payload) {
  const response = await fetch(TODOS_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
}

async function updateTodo(todoId, payload) {
  try {
    const response = await fetch(`${TODOS_URL}/${todoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    await loadTodos();
  } catch (error) {
    setTodoStatus(`Erreur update: ${error.message}`, true);
  }
}

async function deleteTodo(todoId) {
  try {
    const response = await fetch(`${TODOS_URL}/${todoId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    await loadTodos();
  } catch (error) {
    setTodoStatus(`Erreur delete: ${error.message}`, true);
  }
}

refreshBtn.addEventListener("click", loadMachineInfo);
reloadTodosBtn.addEventListener("click", loadTodos);

todoFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const title = titleInputEl.value.trim();
  const description = descriptionInputEl.value.trim();
  if (!title) {
    setTodoStatus("Le titre est obligatoire.", true);
    return;
  }

  try {
    await createTodo({ title, description: description || null });
    titleInputEl.value = "";
    descriptionInputEl.value = "";
    await loadTodos();
  } catch (error) {
    setTodoStatus(`Erreur create: ${error.message}`, true);
  }
});

loadMachineInfo();
loadTodos();
